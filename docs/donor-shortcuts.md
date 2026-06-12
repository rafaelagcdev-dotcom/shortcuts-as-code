# Donor shortcuts: how to harvest actions you can't write by hand

Apple's modern actions — App Intents from Clock, Home, Podcasts, third-party
apps — are undocumented and change with every iOS release. Worse, some of their
parameters are **opaque references** into an app's internal state, not text. You
cannot author those by guessing. You harvest them from a *donor*: a real
shortcut, made on your own device, that already contains the action configured
the way you want.

## When you need a donor

- The action is an **App Intent** (identifier like
  `com.apple.mobiletimer-framework.MobileTimerIntents.MTCreateAlarmIntent`) and
  you don't know its identifier or parameter keys.
- A parameter is an **opaque reference**: a podcast (`WFPodcastShow`), a Home
  scene, a contact, a playlist. These carry internal UUIDs/IDs that only your
  device can produce correctly.

If the action is a plain built-in (text, delay, notification, open app) you can
usually write it by hand from the examples — no donor needed.

## Make a donor (on iPhone/iPad)

1. Shortcuts → **+** → new throwaway shortcut.
2. Add **only the action you want to clone**. Configure it fully — pick the
   podcast, the alarm label, the app, whatever the real shortcut will use.
3. **Share → Copy iCloud Link.**

The link is a normal Apple "shared shortcut" URL. It carries only the actions you
added — nothing else from your device.

## Harvest it

```bash
./tools/harvest.py https://www.icloud.com/shortcuts/<id>          # list actions
./tools/harvest.py <id> --full                                   # full parameters
./tools/harvest.py <id> --json                                   # machine-readable
```

`harvest.py` reads the unsigned plist that Apple's own web preview serves for the
link, and prints each action's identifier and parameters.

### Example: a "Play Podcast" donor

```
# Reproducir podcast — 1 action(s)

[0] is.workflow.actions.playpodcast
    {"WFPodcastShow": {"podcastUUID": "20050B6A-...", "kind": "podcast",
     "collectionName": "Actualidad iPhone",
     "feedUrl": "https://www.actualidadiphone.com/feed/podcast/",
     "collectionId": "483667756"}, "UUID": "..."}
```

That whole `WFPodcastShow` object is the thing you couldn't have typed. Copy it
into your composer (see `examples/commute-mode.py`), drop the donor's `UUID`
(each action gets a fresh one when you compose), and you're done.

## Reuse

Once harvested, an action definition is yours to keep — paste it into any example
composer. Pick in the UI once, harvest once, reuse forever. Building a small
personal library of harvested action dicts beats re-deriving them.

## Notes

- Internal references (`podcastUUID`, scene IDs, contact IDs) may be specific to
  the device that created the donor. If an imported shortcut can't resolve a
  reference, re-harvest from a donor made on the target device.
- Shared-link plists are unsigned by design (that's how the web preview works);
  nothing here breaks a protection. See the README's legal note.
