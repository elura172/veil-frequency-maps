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

The `return-tracks.patch` extension stacks on top of it. Live keeps return tracks
in a list of their own, so none of the `/live/track/*` handlers can reach them.
The patch adds:

```text
/live/song/get/num_return_tracks
/live/song/get/return_track_names
/live/return/get/name <return_index>
/live/return/set/name <return_index> <name>
/live/return/get/num_devices <return_index>
/live/return/get/devices/name <return_index>
/live/return/get/volume <return_index>
/live/return/set/volume <return_index> <value>
/live/return/get/device/parameters/name <return_index> <device_index>
/live/return/get/device/parameters/value <return_index> <device_index>
/live/return/get/device/parameter/value_string <return_index> <device_index> <parameter_index>
/live/return/set/device/parameter/value <return_index> <device_index> <parameter_index> <value>
/live/return/load_device <return_index> <browser_uri>
```

`load_device` resolves the URI against Live's browser and loads it by selecting
the return track, the same mechanism AbletonMCP uses for regular tracks, so no
mouse automation is needed.

Both patches live in `TrackHandler.init_api()` and `SongHandler.init_api()` —
modules that `Manager.reload_imports()` already reloads. Nothing is added to
`manager.py`, which is deliberate: it means `/live/api/reload` activates these
endpoints without restarting Live and without losing an unsaved Set.

The local installation was based on AbletonOSC commit `0ca6821`. The patches are
ordered; `return-tracks.patch` is cut against the crossfader-patched `track.py`.
To reproduce the installation from the repository root:

```sh
git -C "$HOME/Music/Ableton/User Library/Remote Scripts/AbletonOSC" apply \
  "$PWD/integrations/abletonosc/crossfader.patch"
git -C "$HOME/Music/Ableton/User Library/Remote Scripts/AbletonOSC" apply \
  "$PWD/integrations/abletonosc/return-tracks.patch"
```

A full Live restart is the canonical activation procedure. During development
AbletonOSC's `/live/api/reload` endpoint reloads the Python handlers in place,
which is how these endpoints were first brought up against a live Set.
