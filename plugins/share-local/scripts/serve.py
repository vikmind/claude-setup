#!/usr/bin/env python3
"""Serve the share-local folder over HTTP, as configured in ~/.claude/share-local.json."""

import functools
import http.server
import json
from pathlib import Path

CONFIG = Path.home() / ".claude" / "share-local.json"


def main():
    config = json.loads(CONFIG.read_text())
    folder = Path(config["folder"]).expanduser()
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(folder))
    server = http.server.ThreadingHTTPServer((config["bind"], config["port"]), handler)
    server.serve_forever()


if __name__ == "__main__":
    main()
