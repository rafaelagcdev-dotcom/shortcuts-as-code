# Apple Shortcuts as code: harvest, compose, sign, import

Apple Shortcuts has no public API for *creating* shortcuts. The macOS `shortcuts` CLI can run, list and sign them — but not build them. The official path is dragging actions in the editor, one by one, which doesn't scale and can't be automated.

It turns out you can close that gap with four moving parts, none of which require a jailbreak, a developer account, or breaking any protection:

1. **Harvest** real action definitions from any shortcut shared via iCloud link.
2. **Compose** a new shortcut as a plist with those actions.
3. **Sign** it with Apple's own `shortcuts sign` command.
4. **Import** it with one click — and iCloud syncs it to your iPhone and Watch.

I used this to generate, from a chat session with an AI agent on my Mac, a working iPhone shortcut that pauses my car stereo's auto-play and opens Waze when my phone connects to the car's Bluetooth. No editor involved.

## Why harvesting beats a static action catalog

Projects like [Cherri](https://cherrilang.org/) and the older [shortcuts-js](https://github.com/joshfarrant/shortcuts-js) compile code into shortcuts using a built-in catalog of action definitions. That works until you need an action they haven't catalogued — especially the modern **App Intents** that apps expose (Clock, Home, third-party apps), which change with every iOS release and are undocumented.

The harvesting trick sidesteps the catalog entirely: any action that exists *on your own device* can be cloned exactly as your iOS version serializes it.

## Step 1 — Harvest a donor shortcut

Share any shortcut containing the actions you need (Share → Copy iCloud Link). The link serves more than a preview page:

```bash
ID=f66305f6ed41414da51deb1795479b1c   # from https://www.icloud.com/shortcuts/<ID>
curl -s "https://www.icloud.com/shortcuts/api/records/$ID" > record.json
# fields.shortcut.value.downloadURL contains a template URL; substitute ${f}:
URL=$(python3 -c "import json;print(json.load(open('record.json'))['fields']['shortcut']['value']['downloadURL'].replace('\${f}','shortcut.plist'))")
curl -s "$URL" -o donor.plist
```

That's the **unsigned** plist — the same endpoint Apple's own web preview uses, serving content its owner chose to share.

The repo ships [`harvest.py`](harvest.py), which wraps the steps above into one command:

```bash
./harvest.py https://www.icloud.com/shortcuts/<ID>   # list actions, parameters truncated
./harvest.py <ID> --full                             # full parameters
./harvest.py <ID> --json                             # machine-readable
```

Output for a donor containing the Clock app's alarm actions:

```
# Eliminar alarmas — 2 action(s)

[0] com.apple.mobiletimer-framework.MobileTimerIntents.MTGetAlarmsIntent
    {"WFContentItemFilter": ...}
[1] com.apple.mobiletimer.DeleteAlarmIntent
    {...}
```

This is the one piece a static catalog can't give you: **any action that exists on your own device** can be cloned exactly as your iOS version serializes it — including App Intents no project has catalogued. The rest of the pipeline (compose/sign/import) is below; for the compose step a mature option is [Cherri](https://cherrilang.org/).

Or do it inline:

```python
import plistlib, json
d = plistlib.load(open("donor.plist", "rb"))
for a in d["WFWorkflowActions"]:
    print(a["WFWorkflowActionIdentifier"])
    print(json.dumps(a.get("WFWorkflowActionParameters", {}), default=str)[:300])
```

This is how you discover gems like the Clock app's intents, which you will not find documented anywhere:

```
com.apple.mobiletimer-framework.MobileTimerIntents.MTGetAlarmsIntent
com.apple.mobiletimer.DeleteAlarmIntent
com.apple.mobiletimer-framework.MobileTimerIntents.MTCreateAlarmIntent
```

## Step 2 — Compose

A shortcut is a dict with a `WFWorkflowActions` array plus some metadata. The rules that matter:

- Every action gets a fresh `UUID`.
- Actions reference each other's output through attachments: `{"OutputUUID": <uuid of producer>, "Type": "ActionOutput", "OutputName": "..."}` wrapped in `WFTextTokenAttachment` (or embedded in a `WFTextTokenString` for interpolation).
- Control flow (`if`, `repeat`) is a pair/triple of actions sharing a `GroupingIdentifier`, with `WFControlFlowMode` 0 (open), 1 (else), 2 (close).
- The shortcut's own input is the attachment `{"Type": "ExtensionInput"}`, and the workflow needs `WFWorkflowHasShortcutInputVariables: true`.

A complete, working example — pause whatever the car started playing, open Waze, pause again for stereos that send their play command late:

```python
import plistlib, uuid

U = lambda: str(uuid.uuid4()).upper()

def delay(seconds):
    return {"WFWorkflowActionIdentifier": "is.workflow.actions.delay",
            "WFWorkflowActionParameters": {"UUID": U(), "WFDelayTime": seconds}}

def pause():
    return {"WFWorkflowActionIdentifier": "is.workflow.actions.pausemusic",
            "WFWorkflowActionParameters": {"UUID": U(), "WFPlayPauseBehavior": "Pause"}}

open_waze = {"WFWorkflowActionIdentifier": "is.workflow.actions.openapp",
             "WFWorkflowActionParameters": {"UUID": U(),
                 "WFAppIdentifier": "com.waze.iphone",
                 "WFSelectedApp": {"BundleIdentifier": "com.waze.iphone", "Name": "Waze"}}}

notify = {"WFWorkflowActionIdentifier": "is.workflow.actions.notification",
          "WFWorkflowActionParameters": {"UUID": U(), "WFNotificationActionSound": False,
              "WFNotificationActionBody": {
                  "Value": {"string": "🚗 Car mode: autoplay blocked + Waze", "attachmentsByRange": {}},
                  "WFSerializationType": "WFTextTokenString"}}}

workflow = {
    "WFWorkflowActions": [delay(1), pause(), open_waze, delay(3), pause(), notify],
    "WFWorkflowClientVersion": "2607.1.3",
    "WFWorkflowMinimumClientVersion": 900,
    "WFWorkflowMinimumClientVersionString": "900",
    "WFWorkflowIcon": {"WFWorkflowIconStartColor": 4282601983,
                       "WFWorkflowIconGlyphNumber": 59729},
    "WFWorkflowImportQuestions": [], "WFWorkflowTypes": [], "WFQuickActionSurfaces": [],
    "WFWorkflowHasShortcutInputVariables": False,
    "WFWorkflowInputContentItemClasses": ["WFAppContentItem", "WFStringContentItem"],
}
plistlib.dump(workflow, open("Car Mode.shortcut", "wb"))
```

## Step 3 — Sign

```bash
shortcuts sign --mode anyone --input "Car Mode.shortcut" --output "signed/Car Mode.shortcut"
```

This is an official Apple command shipped with macOS. The output filename becomes the shortcut's name on import.

## Step 4 — Import

```bash
open "signed/Car Mode.shortcut"
```

Shortcuts.app pops an "Add Shortcut" dialog — one human click (by design: nobody should be able to silently install shortcuts on your devices) — and iCloud syncs it everywhere. You can even smoke-test on the Mac: `shortcuts run "Car Mode"`.

## Gotchas

- **"Select a value for each parameter"** at runtime means a required parameter is missing from your dict. Some actions need more than the obvious keys (e.g. the file actions want storage-service parameters). When in doubt, harvest a *configured* donor instead of guessing.
- **Personal automations cannot be created this way.** The `.shortcut` format carries no triggers, there's no CLI or URL scheme for automations, and they don't exist in macOS at all. The Bluetooth/time/location trigger is a ~6-tap manual step pointing at your generated shortcut. That's the irreducible toll.
- **Calling shortcuts with input and getting results back**: `shortcuts://x-callback-url/run-shortcut?name=X&input=text&text=...` — pair it with a final "Stop and Output" action and the caller (e.g. a Scriptable script) receives the shortcut's real output in `x-success`. This turns fire-and-forget shortcut calls into verified ones.
- Apple may change the iCloud endpoint or the signed format whenever it likes. This is an undocumented-but-public surface, not a contract.

## Legal note

Nothing here circumvents a technological protection measure: the plist is served unsigned by Apple's endpoint for content its owner shared, `shortcuts sign` is used exactly as intended, and no developer agreement is involved. The one-click import confirmation is a safety property worth keeping.
