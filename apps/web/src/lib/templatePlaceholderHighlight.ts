import { Extension } from "@tiptap/core";
import { Plugin, PluginKey } from "@tiptap/pm/state";
import { Decoration, DecorationSet } from "@tiptap/pm/view";

export const TEMPLATE_PLACEHOLDER_HIGHLIGHT_CLASS = "template-token-highlight";

/** Matches `template_renderer.PLACEHOLDER_PATTERN` (dotted keys). */
export const DOCUMENT_TOKEN_PATTERN =
  /\{\{[a-z][a-z0-9_]*(?:\.[a-z][a-z0-9_]*)*\}\}/g;

/** Old seed tokens. Canonical dotted keys live in `TEMPLATE_PLACEHOLDERS`. */
export const LEGACY_DOCUMENT_PLACEHOLDER_ALIASES: Readonly<
  Record<string, string>
> = {
  patient_name: "patient.full_name",
  visit_date: "visit.date",
};

const TOKEN_TEST = /^\{\{[a-z][a-z0-9_]*(?:\.[a-z][a-z0-9_]*)*\}\}$/;

export function extractPlaceholderKey(token: string): string | null {
  if (!TOKEN_TEST.test(token)) return null;
  return token.slice(2, -2);
}

export function isKnownTemplatePlaceholderToken(
  token: string,
  validKeys?: ReadonlySet<string>,
): boolean {
  const key = extractPlaceholderKey(token);
  if (!key) return false;
  if (!validKeys || validKeys.size === 0) return true;
  if (validKeys.has(key)) return true;
  const alias = LEGACY_DOCUMENT_PLACEHOLDER_ALIASES[key];
  return Boolean(alias && validKeys.has(alias));
}

export function highlightPlaceholdersInHtml(
  html: string,
  validKeys?: ReadonlySet<string>,
): string {
  return html.replace(DOCUMENT_TOKEN_PATTERN, (match) => {
    if (!isKnownTemplatePlaceholderToken(match, validKeys)) return match;
    return `<mark class="${TEMPLATE_PLACEHOLDER_HIGHLIGHT_CLASS}">${match}</mark>`;
  });
}

export function sanitizeTemplateHtml(html: string): string {
  return html.replace(/<\/?(script|iframe|object|embed)[^>]*>/gi, "");
}

export const TemplatePlaceholderHighlight = Extension.create({
  name: "templatePlaceholderHighlight",

  addOptions() {
    return {
      validKeys: undefined as ReadonlySet<string> | undefined,
    };
  },

  addProseMirrorPlugins() {
    const validKeys = this.options.validKeys;
    return [
      new Plugin({
        key: new PluginKey("templatePlaceholderHighlight"),
        props: {
          decorations: (state) => {
            const decorations: Decoration[] = [];
            state.doc.descendants((node, pos) => {
              if (!node.isText || !node.text) return;
              const text = node.text;
              DOCUMENT_TOKEN_PATTERN.lastIndex = 0;
              let match: RegExpExecArray | null;
              while ((match = DOCUMENT_TOKEN_PATTERN.exec(text)) !== null) {
                const token = match[0];
                if (!isKnownTemplatePlaceholderToken(token, validKeys))
                  continue;
                const from = pos + match.index;
                const to = from + token.length;
                decorations.push(
                  Decoration.inline(from, to, {
                    class: TEMPLATE_PLACEHOLDER_HIGHLIGHT_CLASS,
                  }),
                );
              }
            });
            return DecorationSet.create(state.doc, decorations);
          },
        },
      }),
    ];
  },
});
