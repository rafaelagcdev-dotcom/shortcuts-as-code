#!/usr/bin/env python3
"""car-mode.py — compose a "Car Mode" shortcut as a .shortcut file.

This is its own concrete composer: explicit, verifiable, no framework. It builds
a shortcut that, when the phone connects to the car's Bluetooth, pauses whatever
the stereo auto-started, opens Waze, and pauses once more for stereos that send
their play command late.

    python examples/car-mode.py
    ./tools/sign.sh "Car Mode.shortcut"
    open "signed/Car Mode.shortcut"

Then add a Personal Automation (Bluetooth -> your car -> run "Car Mode"); that
trigger is the one manual step Apple does not let you generate.
"""

import plistlib
import uuid

U = lambda: str(uuid.uuid4()).upper()


def delay(seconds):
    return {"WFWorkflowActionIdentifier": "is.workflow.actions.delay",
            "WFWorkflowActionParameters": {"UUID": U(), "WFDelayTime": seconds}}


def pause():
    return {"WFWorkflowActionIdentifier": "is.workflow.actions.pausemusic",
            "WFWorkflowActionParameters": {"UUID": U(), "WFPlayPauseBehavior": "Pause"}}


def open_app(bundle_id, name):
    return {"WFWorkflowActionIdentifier": "is.workflow.actions.openapp",
            "WFWorkflowActionParameters": {"UUID": U(), "WFAppIdentifier": bundle_id,
                "WFSelectedApp": {"BundleIdentifier": bundle_id, "Name": name}}}


def notification(text):
    return {"WFWorkflowActionIdentifier": "is.workflow.actions.notification",
            "WFWorkflowActionParameters": {"UUID": U(), "WFNotificationActionSound": False,
                "WFNotificationActionBody": {
                    "Value": {"string": text, "attachmentsByRange": {}},
                    "WFSerializationType": "WFTextTokenString"}}}


def workflow(actions, glyph=59729, color=4282601983):
    return {
        "WFWorkflowActions": actions,
        "WFWorkflowClientVersion": "2607.1.3",
        "WFWorkflowMinimumClientVersion": 900,
        "WFWorkflowMinimumClientVersionString": "900",
        "WFWorkflowIcon": {"WFWorkflowIconStartColor": color, "WFWorkflowIconGlyphNumber": glyph},
        "WFWorkflowImportQuestions": [], "WFWorkflowTypes": [], "WFQuickActionSurfaces": [],
        "WFWorkflowHasShortcutInputVariables": False,
        "WFWorkflowInputContentItemClasses": ["WFAppContentItem", "WFStringContentItem"],
    }


def main():
    actions = [
        delay(1),
        pause(),
        open_app("com.waze.iphone", "Waze"),
        delay(3),
        pause(),
        notification("\U0001F697 Car mode: autoplay blocked + Waze"),
    ]
    out = "Car Mode.shortcut"
    plistlib.dump(workflow(actions), open(out, "wb"))
    print(f"wrote {out} ({len(actions)} actions) — now: ./tools/sign.sh \"{out}\"")


if __name__ == "__main__":
    main()
