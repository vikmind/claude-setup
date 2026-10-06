# share-local

Saves artifacts (HTML pages, reports, diagrams, files) into a folder that a
local web server publishes, and gives back the link. Use it instead of
publishing to claude.ai when the page should stay on your machine or your
tailnet.

Two skills:

- `/share-local:setup` asks for the folder, the port, and who can open the
  links, then starts the server at login.
- `/share-local:share` writes an artifact into the folder and replies with its
  URL.

macOS only, because the server runs as a launchd login agent.

## How it works

1. `scripts/install.py` saves the settings to `~/.claude/share-local.json`,
   writes `~/Library/LaunchAgents/com.claude-setup.share-local.plist`, and
   loads it. With Tailscale enabled, it also runs
   `tailscale serve --bg --http=<port> http://127.0.0.1:<port>`.
2. The launchd agent runs `scripts/serve.py` from the newest installed plugin
   version, so a plugin upgrade needs no new setup. `serve.py` reads the same
   settings file and serves the folder with Python's `http.server`.
3. `/share-local:share` reads `folder` and `url` from the settings file.

The settings file looks like this:

```json
{
  "folder": "/Users/you/share",
  "port": 3333,
  "bind": "127.0.0.1",
  "tailscale": true,
  "url": "http://your-mac.your-tailnet.ts.net:3333"
}
```

### Why Tailscale goes through `tailscale serve`

With Tailscale enabled, the server listens on `127.0.0.1` only, and
`tailscale serve` forwards tailnet traffic to it. A server bound directly to
the Tailscale address does not work when the macOS firewall is on: the firewall
asks before it lets Python accept connections, and a launchd agent cannot show
that prompt, so the firewall drops the connections. Tailscale is already
allowed through the firewall.

The same firewall problem applies to the `Local network` option
(`0.0.0.0`). If links do not open from other devices, allow Python in
System Settings > Network > Firewall > Options.

## Install

1. Add this repo as marketplace:

   ```
   /plugin marketplace add vikmind/claude-setup
   ```

2. Install `share-local`:

   ```
   /plugin install share-local@claude-setup
   ```

3. Run `/share-local:setup` and answer the questions. Run it again to change
   the settings.

## Uninstall

```
launchctl bootout gui/$(id -u)/com.claude-setup.share-local
rm ~/Library/LaunchAgents/com.claude-setup.share-local.plist ~/.claude/share-local.json
tailscale serve --http=<port> off   # only if Tailscale was enabled
```

## Requirements

macOS, python3, and the Tailscale CLI for the Tailscale option.
