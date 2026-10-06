---
description: Set up share-local - ask for the folder, port, address, and Tailscale use, save them to ~/.claude/share-local.json, and start the web server at login. Use when the user runs /share-local:setup or wants to change those settings.
---

# /share-local:setup

Configure the local web server that `/share-local:share` puts artifacts into. macOS only.

## Steps

1. If `~/.claude/share-local.json` exists, read it and use its values as the defaults below.

2. Ask with one AskUserQuestion call (four questions):
   - **Folder**: the folder to serve. Options: the current value if any, `~/share`. The user can type another path with "Other".
   - **Port**: options: the current value if any, `3333`, `8080`.
   - **Access**: who can open the links.
     - `Tailscale (tailnet)`: devices on the user's tailnet. The server listens on localhost and `tailscale serve` forwards port traffic to it.
     - `This Mac only`: listens on `127.0.0.1`.
     - `Local network`: listens on `0.0.0.0`. Warn that anyone on the same network can read the folder, and that the macOS firewall can block it (see the plugin README).
     A custom listen address typed with "Other" is passed as `--bind`.
   - **Shortcut**: add a `/share` command as a shortcut for `/share-local:share`? Options: `Yes`, `No`.
     Plugin commands always carry the plugin prefix, so the shortcut is a personal skill at
     `~/.claude/skills/share/SKILL.md`. Skip this question if that file already exists.

3. Find the newest installed script:
   `ls -dt ~/.claude/plugins/cache/claude-setup/share-local/*/scripts/install.py | head -1`

4. Run it with the answers:
   ```
   python3 "<install.py>" --folder "<folder>" --port <port> --bind <address> --tailscale on|off
   ```
   Use `--tailscale on` for the Tailscale option, and `--tailscale off --bind 127.0.0.1` or `--bind 0.0.0.0` for the others.
   The script saves `~/.claude/share-local.json`, writes the launchd agent
   `~/Library/LaunchAgents/com.claude-setup.share-local.plist`, starts it, and configures `tailscale serve`.

5. If the user chose the shortcut, write `~/.claude/skills/share/SKILL.md` with exactly this content:
   ```
   ---
   description: Shortcut for /share-local:share - save an artifact into the share-local folder and give back its URL.
   ---

   Invoke the `share-local:share` skill with the same arguments, and follow it.
   ```
   Tell the user that `/share` appears in new sessions.

6. Report the base URL that the script prints, or its error output if it fails.
   If another process already uses the port, say so and offer to rerun with a different port.
