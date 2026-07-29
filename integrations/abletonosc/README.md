# AbletonOSC integration

The generic MCP uses upstream [AbletonOSC](https://github.com/ideoforms/AbletonOSC) plus the small, versioned `crossfader.patch` extension.

The patch adds these local OSC endpoints:

```text
/live/song/get/crossfader
/live/song/set/crossfader <value -1..1>
/live/track/get/crossfade_assign <track_index>
/live/track/set/crossfade_assign <track_index> <0|1|2>
```

Track assignment values follow Live's enum: `0 = A`, `1 = none`, `2 = B`.

The local installation was based on AbletonOSC commit `0ca6821`. To reproduce it from the repository root:

```sh
git -C "$HOME/Music/Ableton/User Library/Remote Scripts/AbletonOSC" apply \
  "$PWD/integrations/abletonosc/crossfader.patch"
```

Restart Live after applying the patch. During development, AbletonOSC's `/live/api/reload` endpoint may reload Python handlers, but a full Live restart is the canonical activation procedure.
