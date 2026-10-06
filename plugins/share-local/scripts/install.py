#!/usr/bin/env python3
"""Save the share-local settings, run the server as a launchd login agent, and
expose it on the tailnet when Tailscale is enabled. macOS only.

Usage: install.py --folder DIR --port N --bind ADDR --tailscale on|off
"""

import argparse
import json
import os
import shutil
import socket
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

CONFIG = Path.home() / ".claude" / "share-local.json"
LABEL = "com.claude-setup.share-local"
PLIST = Path.home() / "Library" / "LaunchAgents" / f"{LABEL}.plist"
LOG = Path.home() / "Library" / "Logs" / "share-local.log"
# Point at the newest installed plugin version, so plugin upgrades need no reinstall.
SERVE = 'exec "{python}" "$(ls -dt ~/.claude/plugins/cache/claude-setup/share-local/*/scripts/serve.py | head -1)"'


def tailscale_bin():
    app = "/Applications/Tailscale.app/Contents/MacOS/Tailscale"
    return shutil.which("tailscale") or (app if os.path.exists(app) else None)


def tailscale(*args):
    binary = tailscale_bin()
    if not binary:
        sys.exit("Tailscale is enabled, but the tailscale CLI was not found.")
    return subprocess.run([binary, *args], capture_output=True, text=True, check=True).stdout


def write_plist(python):
    PLIST.parent.mkdir(parents=True, exist_ok=True)
    LOG.parent.mkdir(parents=True, exist_ok=True)
    PLIST.write_text(f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>{LABEL}</string>
  <key>ProgramArguments</key>
  <array>
    <string>/bin/zsh</string>
    <string>-c</string>
    <string>{SERVE.format(python=python)}</string>
  </array>
  <key>RunAtLoad</key><true/>
  <key>KeepAlive</key><true/>
  <key>StandardOutPath</key><string>{LOG}</string>
  <key>StandardErrorPath</key><string>{LOG}</string>
</dict>
</plist>
""")


def reload_agent():
    domain = f"gui/{os.getuid()}"
    subprocess.run(["launchctl", "bootout", f"{domain}/{LABEL}"], capture_output=True)
    for _ in range(50):
        if subprocess.run(["launchctl", "print", f"{domain}/{LABEL}"], capture_output=True).returncode:
            break
        time.sleep(0.1)
    subprocess.run(["launchctl", "bootstrap", domain, str(PLIST)], check=True)


def base_url(config):
    port = config["port"]
    if config["tailscale"]:
        name = json.loads(tailscale("status", "--json"))["Self"]["DNSName"].rstrip(".")
        return f"http://{name}:{port}"
    if config["bind"] in ("127.0.0.1", "localhost"):
        return f"http://localhost:{port}"
    if config["bind"] in ("0.0.0.0", ""):
        return f"http://{socket.gethostname()}:{port}"
    return f"http://{config['bind']}:{port}"


def check(config):
    host = "127.0.0.1" if config["bind"] in ("0.0.0.0", "") else config["bind"]
    for _ in range(20):
        try:
            urllib.request.urlopen(f"http://{host}:{config['port']}/", timeout=1)
            return True
        except OSError:
            time.sleep(0.5)
    return False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--folder", required=True)
    parser.add_argument("--port", type=int, required=True)
    parser.add_argument("--bind", default="127.0.0.1")
    parser.add_argument("--tailscale", choices=["on", "off"], required=True)
    args = parser.parse_args()

    if sys.platform != "darwin":
        sys.exit("share-local supports macOS only (it runs the server with launchd).")

    old = json.loads(CONFIG.read_text()) if CONFIG.exists() else {}
    config = {
        "folder": str(Path(args.folder).expanduser().resolve()),
        "port": args.port,
        # Tailscale forwards tailnet traffic to localhost, so the server itself stays local.
        "bind": "127.0.0.1" if args.tailscale == "on" else args.bind,
        "tailscale": args.tailscale == "on",
    }

    if old.get("tailscale") and tailscale_bin():
        subprocess.run([tailscale_bin(), "serve", f"--http={old['port']}", "off"], capture_output=True)
    if config["tailscale"]:
        tailscale("serve", "--bg", f"--http={config['port']}", f"http://127.0.0.1:{config['port']}")

    config["url"] = base_url(config)
    Path(config["folder"]).mkdir(parents=True, exist_ok=True)
    CONFIG.parent.mkdir(parents=True, exist_ok=True)
    CONFIG.write_text(json.dumps(config, indent=2) + "\n")

    write_plist(shutil.which("python3") or sys.executable)
    reload_agent()

    print(json.dumps(config, indent=2))
    if not check(config):
        sys.exit(f"The server does not respond. See {LOG}.")
    print(f"Server is up: {config['url']}/")


if __name__ == "__main__":
    main()
