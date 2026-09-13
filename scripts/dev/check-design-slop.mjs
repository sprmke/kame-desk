#!/usr/bin/env node
/**
 * Deterministic anti-slop checks (AST/text, no LLM).
 * Ratchet: fail if any rule count exceeds docs/workflow/baselines/design-slop-baseline.json.
 *
 * Override a file+rule with a written reason in scripts/dev/design-slop-overrides.txt
 * (tab-separated: relativePath  RULE  reason).
 */
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../..");
const SRC = path.join(ROOT, "apps/web/src");
const STYLES_REL = "apps/web/src/styles.css";
const BASELINE_PATH = path.join(
  ROOT,
  "docs/workflow/baselines/design-slop-baseline.json",
);
const OVERRIDE_PATH = path.join(ROOT, "scripts/dev/design-slop-overrides.txt");

const BANNED_ICONS = [
  "Stethoscope",
  "Armchair",
  "Bot",
  "Sparkles",
  "CalendarClock",
  "Briefcase",
  "Rocket",
];

const writeBaseline = process.argv.includes("--write-baseline");
const listAll = process.argv.includes("--list");

function walk(dir, acc = []) {
  for (const ent of fs.readdirSync(dir, { withFileTypes: true })) {
    const p = path.join(dir, ent.name);
    if (ent.isDirectory()) walk(p, acc);
    else if (/\.(tsx?|css)$/.test(ent.name)) acc.push(p);
  }
  return acc;
}

function rel(p) {
  return path.relative(ROOT, p).split(path.sep).join("/");
}

function parseOverrides() {
  /** @type {Map<string, string>} */
  const map = new Map();
  if (!fs.existsSync(OVERRIDE_PATH)) return map;
  for (const raw of fs.readFileSync(OVERRIDE_PATH, "utf8").split("\n")) {
    const line = raw.trim();
    if (!line || line.startsWith("#")) continue;
    const [file, rule, ...reasonParts] = line.split("\t");
    const reason = reasonParts.join("\t").trim();
    if (!file || !rule || !reason) {
      console.error(`OVERRIDE: malformed line: ${raw}`);
      process.exit(2);
    }
    map.set(`${file}::${rule}`, reason);
  }
  return map;
}

function lineNo(source, index) {
  return source.slice(0, index).split("\n").length;
}

function addFinding(findings, file, rule, index, source, detail) {
  findings.push({
    file,
    rule,
    line: lineNo(source, index),
    detail,
  });
}

function scanFile(fileRel, source, findings) {
  const isStyles = fileRel === STYLES_REL;
  const isTsx = fileRel.endsWith(".tsx") || fileRel.endsWith(".ts");

  if (isTsx) {
    for (const name of BANNED_ICONS) {
      const re = new RegExp(`\\b${name}\\b`, "g");
      let m;
      while ((m = re.exec(source))) {
        addFinding(
          findings,
          fileRel,
          name === "Bot" || name === "Sparkles" ? "B4" : "B3",
          m.index,
          source,
          name,
        );
      }
    }

    let m;
    const statRe = /\bStatCard\b/g;
    while ((m = statRe.exec(source))) {
      addFinding(findings, fileRel, "B1", m.index, source, "StatCard");
    }

    const descRe = /<PageHeader[\s\S]{0,400}?\bdescription=/g;
    while ((m = descRe.exec(source))) {
      addFinding(
        findings,
        fileRel,
        "B7",
        m.index,
        source,
        "PageHeader description",
      );
    }

    const tripleRe =
      /className=\{?[`'"][^`'"]*\brounded-2xl\b[^`'"]*\bborder\b[^`'"]*\bshadow(?:-|\/|$|\s)[^`'"]*[`'"]/g;
    while ((m = tripleRe.exec(source))) {
      addFinding(
        findings,
        fileRel,
        "H3",
        m.index,
        source,
        "rounded-2xl + border + shadow",
      );
    }

    const hoverRevealRe =
      /(?:opacity-0|invisible|hidden)[^"'`\n]{0,80}hover:(?:opacity-100|visible|block|flex)/g;
    while ((m = hoverRevealRe.exec(source))) {
      addFinding(
        findings,
        fileRel,
        "M6",
        m.index,
        source,
        "affordance revealed only on hover",
      );
    }

    if (
      /[₱]|formatCurrency|formatMoney|toLocaleString\(\s*['"]en-PH/.test(
        source,
      ) &&
      !/tabular-nums/.test(source)
    ) {
      addFinding(
        findings,
        fileRel,
        "T9",
        0,
        source,
        "money/number formatting without tabular-nums in this file",
      );
    }
  }

  if (!isStyles) {
    const hexRe = /#[0-9a-fA-F]{3,8}\b/g;
    let m;
    while ((m = hexRe.exec(source))) {
      const before = source.slice(Math.max(0, m.index - 80), m.index);
      if (before.includes("http") || before.includes("file:")) continue;
      addFinding(findings, fileRel, "T11", m.index, source, m[0]);
    }
    const rgbRe = /\brgba?\(/g;
    while ((m = rgbRe.exec(source))) {
      addFinding(findings, fileRel, "T11", m.index, source, "rgb()");
    }
  }
}

function countByRule(findings) {
  /** @type {Record<string, number>} */
  const counts = {};
  for (const f of findings) {
    counts[f.rule] = (counts[f.rule] ?? 0) + 1;
  }
  return counts;
}

function main() {
  const overrides = parseOverrides();
  const files = walk(SRC);
  /** @type {{file: string, rule: string, line: number, detail: string}[]} */
  let findings = [];
  for (const abs of files) {
    const fileRel = rel(abs);
    const source = fs.readFileSync(abs, "utf8");
    scanFile(fileRel, source, findings);
  }

  const suppressed = [];
  findings = findings.filter((f) => {
    const key = `${f.file}::${f.rule}`;
    if (overrides.has(key)) {
      suppressed.push({ ...f, reason: overrides.get(key) });
      return false;
    }
    return true;
  });

  const counts = countByRule(findings);
  const total = findings.length;

  if (writeBaseline) {
    const payload = {
      generatedAt: new Date().toISOString(),
      total,
      counts,
      note: "Ratchet: check:design-slop fails if any rule count increases. Re-run with --write-baseline after intentional reductions.",
    };
    fs.mkdirSync(path.dirname(BASELINE_PATH), { recursive: true });
    fs.writeFileSync(BASELINE_PATH, `${JSON.stringify(payload, null, 2)}\n`);
    console.log(`Wrote baseline (${total} findings) → ${rel(BASELINE_PATH)}`);
    return;
  }

  if (listAll) {
    for (const f of findings) {
      console.log(`${f.file}:${f.line}\t${f.rule}\t${f.detail}`);
    }
  }

  console.log(`check:design-slop — ${total} finding(s) after overrides`);
  const rules = Object.keys(counts).sort();
  for (const rule of rules) {
    console.log(`  ${rule}: ${counts[rule]}`);
  }
  if (suppressed.length) {
    console.log(`  overrides applied: ${suppressed.length}`);
  }

  if (!fs.existsSync(BASELINE_PATH)) {
    console.error(
      "No baseline at docs/workflow/baselines/design-slop-baseline.json. Run with --write-baseline once.",
    );
    process.exit(1);
  }

  const baseline = JSON.parse(fs.readFileSync(BASELINE_PATH, "utf8"));
  const baseCounts = baseline.counts ?? {};
  const allRules = new Set([...Object.keys(baseCounts), ...Object.keys(counts)]);
  const increased = [];
  const decreased = [];
  for (const rule of allRules) {
    const now = counts[rule] ?? 0;
    const was = baseCounts[rule] ?? 0;
    if (now > was) increased.push(`${rule} ${was}→${now}`);
    if (now < was) decreased.push(`${rule} ${was}→${now}`);
  }

  if (decreased.length) {
    console.log(
      `Counts dropped (${decreased.join(", ")}). Consider: node scripts/dev/check-design-slop.mjs --write-baseline`,
    );
  }

  if (increased.length) {
    console.error(`DESIGN SLOP RATCHET: counts increased: ${increased.join(", ")}`);
    const sample = findings.filter((f) =>
      increased.some((s) => s.startsWith(f.rule + " ")),
    );
    for (const f of sample.slice(0, 20)) {
      console.error(`  ${f.file}:${f.line} ${f.rule} ${f.detail}`);
    }
    process.exit(1);
  }

  console.log("OK — design-slop counts within baseline");
}

main();
