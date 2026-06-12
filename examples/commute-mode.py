#!/usr/bin/env python3
"""commute-mode.py — compose a "Commute Mode" shortcut as a .shortcut file.

Plays a news podcast and opens the browser. The point of this example is the
podcast reference: "Play Podcast" stores the show as an opaque WFPodcastShow
object (podcastUUID / feedUrl / collectionId), NOT its name. You cannot type it
correctly — you harvest it from a donor where you picked the show in the UI:

    ./tools/harvest.py https://www.icloud.com/shortcuts/<your-donor-id>

Then paste the whole WFPodcastShow object below. See docs/donor-shortcuts.md.

    python examples/commute-mode.py
    ./tools/sign.sh "Commute Mode.shortcut"
    open "signed/Commute Mode.shortcut"
"""

import plistlib
import uuid

U = lambda: str(uuid.uuid4()).upper()

# Harvested from a donor shortcut — do not hand-edit; harvest your own show.
PODCAST_SHOW = {
    "podcastUUID": "20050B6A-787C-4211-B051-EA94DF617CCD",
    "kind": "podcast",
    "collectionName": "Actualidad iPhone",
    "feedUrl": "https://www.actualidadiphone.com/feed/podcast/",
    "collectionId": "483667756",
}


def play_podcast(show):
    return {"WFWorkflowActionIdentifier": "is.workflow.actions.playpodcast",
            "WFWorkflowActionParameters": {"UUID": U(), "WFPodcastShow": show}}


def open_app(bundle_id, name):
    return {"WFWorkflowActionIdentifier": "is.workflow.actions.openapp",
            "WFWorkflowActionParameters": {"UUID": U(), "WFAppIdentifier": bundle_id,
                "WFSelectedApp": {"BundleIdentifier": bundle_id, "Name": name}}}


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
        play_podcast(PODCAST_SHOW),
        open_app("com.apple.mobilesafari", "Safari"),
    ]
    out = "Commute Mode.shortcut"
    plistlib.dump(workflow(actions), open(out, "wb"))
    print(f"wrote {out} ({len(actions)} actions) — now: ./tools/sign.sh \"{out}\"")


if __name__ == "__main__":
    main()
