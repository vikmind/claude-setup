---
description: Save an artifact (HTML page, report, diagram, file) into the share-local folder and give back its URL, instead of publishing it to claude.ai. Use when the user runs /share-local:share or asks to share something locally.
---

# /share-local:share

Place the artifact in the share-local folder and give the user its URL.

## Steps

1. Read `~/.claude/share-local.json`. It has `folder` (where to write) and `url` (the base URL).
   If the file does not exist, tell the user to run `/share-local:setup` first, and stop.
2. Decide what to save. If the user passed arguments, they describe the artifact. Otherwise use the most recent artifact or output in this conversation. If that is unclear, ask.
3. Pick a short kebab-case file name that describes the content, for example `q3-churn-report.html`. Do not overwrite an existing file unless the user asks. If the name is taken, add `-2`, `-3`, and so on.
4. Write the file into `folder`.
   - Pages are self-contained `.html` files: inline CSS and JS, and a `<title>`. Load external scripts from a CDN only when needed.
   - If the artifact needs several files (images, data, extra pages), put them in a subfolder `<folder>/<name>/` with an `index.html`, and use relative paths.
   - Other formats (`.md`, `.json`, `.csv`, `.svg`, images) are saved as they are.
5. Check that the server returns the file:
   `curl -s -o /dev/null -w '%{http_code}' "<url>/<file>"` should print `200`.
   If it does not, restart the server with `launchctl kickstart -k gui/$(id -u)/com.claude-setup.share-local` and check again.
   If it still fails, suggest `/share-local:setup`.
6. Reply with the link: `<url>/<file>`, or `<url>/<name>/` for a folder.

Do not use the Artifact tool to publish to claude.ai when this skill is invoked.
