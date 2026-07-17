# AbletonMCP integration

AbletonMCP provides the localhost TCP `9877` fallback used for browser loading
and core Live operations. The versioned `user-library.patch` extends its browser
resolver to include Live's indexed User Library. This makes custom `.amxd`
devices loadable by their stable `device:m4l:*` URI without mouse automation.
It also accepts exact browser-name selectors such as `name:808 Core Kit` for
factory presets whose `query:*` URI is not exposed consistently by Live.

To reproduce the local installation from the repository root:

```sh
git -C "$HOME/Music/Ableton/User Library/Remote Scripts/AbletonMCP" apply \
  "$PWD/integrations/abletonmcp/user-library.patch"
```

Restart Live after applying the patch so the Control Surface reloads its Python
module. The browser index itself does not need rebuilding.
