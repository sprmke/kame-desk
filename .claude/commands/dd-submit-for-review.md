# dd-submit-for-review

After `/dd-check-before-pr` passes:

```bash
git push -u origin HEAD
gh pr create --fill
```

Target branch: `main` (adjust if team uses `develop`).
