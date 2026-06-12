#!/usr/bin/env python3
"""harvest — extract real action definitions from a shared Apple Shortcut.

Apple's modern actions (App Intents from Clock, Home, third-party apps) are
undocumented and change with every iOS release. The only reliable source for an
action's exact identifier and parameters is a shortcut that already contains it.

This script takes an iCloud share link (Share -> Copy iCloud Link) and prints
every action in the donor shortcut, so you can clone those exact dicts when
composing a new shortcut programmatically.

Usage:
    ./harvest.py <icloud-url-or-id>
    ./harvest.py <url> --full         # full parameters, not truncated
    ./harvest.py <url> --json         # machine-readable output

Example:
    ./harvest.py https://www.icloud.com/shortcuts/3c0961fc689744928684f7a199762062
"""

import argparse
import json
import plistlib
import re
import sys
import urllib.request

RECORD_API = "https://www.icloud.com/shortcuts/api/records/{id}"


def extract_id(arg: str) -> str:
    """Accept a full iCloud URL or a bare 32-hex id."""
    m = re.search(r"shortcuts/([0-9a-fA-F]{32})", arg) or re.fullmatch(
        r"[0-9a-fA-F]{32}", arg.strip()
    )
    if not m:
        sys.exit(f"error: '{arg}' is not a valid iCloud shortcut link or id")
    return m.group(1) if m.re.groups else m.group(0)


def fetch(url: str) -> bytes:
    try:
        with urllib.request.urlopen(url, timeout=20) as r:
            return r.read()
    except Exception as e:  # noqa: BLE001 - surface any network/HTTP failure plainly
        sys.exit(f"error fetching {url}: {e}")


def harvest(shortcut_id: str):
    record = json.loads(fetch(RECORD_API.format(id=shortcut_id)))
    fields = record.get("fields", {})
    name = fields.get("name", {}).get("value", "(unnamed)")
    dl = fields.get("shortcut", {}).get("value", {}).get("downloadURL")
    if not dl:
        sys.exit("error: no downloadURL in record (link expired or not public?)")
    # The record serves a template URL with a ${f} placeholder.
    plist_url = dl.replace("${f}", "shortcut.plist")
    data = plistlib.loads(fetch(plist_url))
    return name, data.get("WFWorkflowActions", [])


def main():
    ap = argparse.ArgumentParser(description="Harvest action definitions from a shared Apple Shortcut.")
    ap.add_argument("link", help="iCloud share link or 32-hex shortcut id")
    ap.add_argument("--full", action="store_true", help="print full parameters (not truncated)")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    args = ap.parse_args()

    name, actions = harvest(extract_id(args.link))

    if args.json:
        out = [
            {
                "index": i,
                "identifier": a.get("WFWorkflowActionIdentifier"),
                "parameters": a.get("WFWorkflowActionParameters", {}),
            }
            for i, a in enumerate(actions)
        ]
        print(json.dumps({"name": name, "actions": out}, default=str, ensure_ascii=False, indent=2))
        return

    print(f"# {name} — {len(actions)} action(s)\n")
    for i, a in enumerate(actions):
        ident = a.get("WFWorkflowActionIdentifier", "?")
        params = json.dumps(a.get("WFWorkflowActionParameters", {}), default=str, ensure_ascii=False)
        if not args.full and len(params) > 300:
            params = params[:300] + " …"
        print(f"[{i}] {ident}")
        print(f"    {params}")


if __name__ == "__main__":
    main()
