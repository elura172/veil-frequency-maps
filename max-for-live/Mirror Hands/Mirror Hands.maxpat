{
  "patcher": {
    "fileversion": 1,
    "appversion": {
      "major": 9,
      "minor": 0,
      "revision": 7,
      "architecture": "x64",
      "modernui": 1
    },
    "classnamespace": "box",
    "rect": [
      40.0,
      80.0,
      1000.0,
      640.0
    ],
    "openinpresentation": 1,
    "devicewidth": 690.0,
    "default_fontsize": 11.0,
    "default_fontname": "Ableton Sans Medium Regular",
    "boxes": [
      {
        "box": {
          "id": "audio-in",
          "maxclass": "newobj",
          "patching_rect": [
            25.0,
            560.0,
            55.0,
            22.0
          ],
          "text": "plugin~"
        }
      },
      {
        "box": {
          "id": "audio-out",
          "maxclass": "newobj",
          "patching_rect": [
            100.0,
            560.0,
            60.0,
            22.0
          ],
          "text": "plugout~"
        }
      },
      {
        "box": {
          "id": "title",
          "maxclass": "comment",
          "patching_rect": [
            25.0,
            20.0,
            180.0,
            24.0
          ],
          "text": "MIRROR HANDS",
          "fontsize": 16.0,
          "presentation": 1,
          "presentation_rect": [
            14.0,
            8.0,
            170.0,
            24.0
          ]
        }
      },
      {
        "box": {
          "id": "sub",
          "maxclass": "comment",
          "patching_rect": [
            25.0,
            48.0,
            260.0,
            18.0
          ],
          "text": "six fuzzy currents \u2192 live.remote~",
          "presentation": 1,
          "presentation_rect": [
            14.0,
            32.0,
            260.0,
            18.0
          ]
        }
      },
      {
        "box": {
          "id": "rx",
          "maxclass": "newobj",
          "patching_rect": [
            25.0,
            95.0,
            105.0,
            22.0
          ],
          "text": "udpreceive 9000"
        }
      },
      {
        "box": {
          "id": "engine",
          "maxclass": "newobj",
          "patching_rect": [
            240.0,
            135.0,
            120.0,
            22.0
          ],
          "text": "js mirror_hands.js"
        }
      },
      {
        "box": {
          "id": "load",
          "maxclass": "newobj",
          "patching_rect": [
            380.0,
            95.0,
            60.0,
            22.0
          ],
          "text": "loadbang"
        }
      },
      {
        "box": {
          "id": "loadmsg",
          "maxclass": "message",
          "patching_rect": [
            460.0,
            95.0,
            65.0,
            22.0
          ],
          "text": "loadbang"
        }
      },
      {
        "box": {
          "id": "status",
          "maxclass": "newobj",
          "patching_rect": [
            800.0,
            135.0,
            155.0,
            22.0
          ],
          "text": "udpsend 127.0.0.1 9001"
        }
      },
      {
        "box": {
          "id": "line-0",
          "maxclass": "newobj",
          "patching_rect": [
            25.0,
            205.0,
            60.0,
            22.0
          ],
          "text": "line~ 0."
        }
      },
      {
        "box": {
          "id": "remote-0",
          "maxclass": "newobj",
          "patching_rect": [
            105.0,
            205.0,
            165.0,
            22.0
          ],
          "text": "live.remote~ @normalized 1"
        }
      },
      {
        "box": {
          "id": "dial-0",
          "maxclass": "live.dial",
          "patching_rect": [
            300.0,
            205.0,
            48.0,
            42.0
          ],
          "parameter_enable": 0,
          "presentation": 1,
          "presentation_rect": [
            285.0,
            8.0,
            48.0,
            42.0
          ]
        }
      },
      {
        "box": {
          "id": "label-0",
          "maxclass": "comment",
          "patching_rect": [
            360.0,
            205.0,
            90.0,
            18.0
          ],
          "text": "ENERGY",
          "presentation": 1,
          "presentation_rect": [
            281.0,
            51.0,
            62.0,
            16.0
          ]
        }
      },
      {
        "box": {
          "id": "led-0",
          "maxclass": "led",
          "patching_rect": [
            470.0,
            205.0,
            16.0,
            16.0
          ],
          "presentation": 1,
          "presentation_rect": [
            301.0,
            69.0,
            16.0,
            16.0
          ]
        }
      },
      {
        "box": {
          "id": "line-1",
          "maxclass": "newobj",
          "patching_rect": [
            25.0,
            257.0,
            60.0,
            22.0
          ],
          "text": "line~ 0."
        }
      },
      {
        "box": {
          "id": "remote-1",
          "maxclass": "newobj",
          "patching_rect": [
            105.0,
            257.0,
            165.0,
            22.0
          ],
          "text": "live.remote~ @normalized 1"
        }
      },
      {
        "box": {
          "id": "dial-1",
          "maxclass": "live.dial",
          "patching_rect": [
            300.0,
            257.0,
            48.0,
            42.0
          ],
          "parameter_enable": 0,
          "presentation": 1,
          "presentation_rect": [
            351.0,
            8.0,
            48.0,
            42.0
          ]
        }
      },
      {
        "box": {
          "id": "label-1",
          "maxclass": "comment",
          "patching_rect": [
            360.0,
            257.0,
            90.0,
            18.0
          ],
          "text": "BRIGHTNESS",
          "presentation": 1,
          "presentation_rect": [
            347.0,
            51.0,
            62.0,
            16.0
          ]
        }
      },
      {
        "box": {
          "id": "led-1",
          "maxclass": "led",
          "patching_rect": [
            470.0,
            257.0,
            16.0,
            16.0
          ],
          "presentation": 1,
          "presentation_rect": [
            367.0,
            69.0,
            16.0,
            16.0
          ]
        }
      },
      {
        "box": {
          "id": "line-2",
          "maxclass": "newobj",
          "patching_rect": [
            25.0,
            309.0,
            60.0,
            22.0
          ],
          "text": "line~ 0."
        }
      },
      {
        "box": {
          "id": "remote-2",
          "maxclass": "newobj",
          "patching_rect": [
            105.0,
            309.0,
            165.0,
            22.0
          ],
          "text": "live.remote~ @normalized 1"
        }
      },
      {
        "box": {
          "id": "dial-2",
          "maxclass": "live.dial",
          "patching_rect": [
            300.0,
            309.0,
            48.0,
            42.0
          ],
          "parameter_enable": 0,
          "presentation": 1,
          "presentation_rect": [
            417.0,
            8.0,
            48.0,
            42.0
          ]
        }
      },
      {
        "box": {
          "id": "label-2",
          "maxclass": "comment",
          "patching_rect": [
            360.0,
            309.0,
            90.0,
            18.0
          ],
          "text": "WARMTH",
          "presentation": 1,
          "presentation_rect": [
            413.0,
            51.0,
            62.0,
            16.0
          ]
        }
      },
      {
        "box": {
          "id": "led-2",
          "maxclass": "led",
          "patching_rect": [
            470.0,
            309.0,
            16.0,
            16.0
          ],
          "presentation": 1,
          "presentation_rect": [
            433.0,
            69.0,
            16.0,
            16.0
          ]
        }
      },
      {
        "box": {
          "id": "line-3",
          "maxclass": "newobj",
          "patching_rect": [
            25.0,
            361.0,
            60.0,
            22.0
          ],
          "text": "line~ 0."
        }
      },
      {
        "box": {
          "id": "remote-3",
          "maxclass": "newobj",
          "patching_rect": [
            105.0,
            361.0,
            165.0,
            22.0
          ],
          "text": "live.remote~ @normalized 1"
        }
      },
      {
        "box": {
          "id": "dial-3",
          "maxclass": "live.dial",
          "patching_rect": [
            300.0,
            361.0,
            48.0,
            42.0
          ],
          "parameter_enable": 0,
          "presentation": 1,
          "presentation_rect": [
            483.0,
            8.0,
            48.0,
            42.0
          ]
        }
      },
      {
        "box": {
          "id": "label-3",
          "maxclass": "comment",
          "patching_rect": [
            360.0,
            361.0,
            90.0,
            18.0
          ],
          "text": "SHIMMER",
          "presentation": 1,
          "presentation_rect": [
            479.0,
            51.0,
            62.0,
            16.0
          ]
        }
      },
      {
        "box": {
          "id": "led-3",
          "maxclass": "led",
          "patching_rect": [
            470.0,
            361.0,
            16.0,
            16.0
          ],
          "presentation": 1,
          "presentation_rect": [
            499.0,
            69.0,
            16.0,
            16.0
          ]
        }
      },
      {
        "box": {
          "id": "line-4",
          "maxclass": "newobj",
          "patching_rect": [
            25.0,
            413.0,
            60.0,
            22.0
          ],
          "text": "line~ 0."
        }
      },
      {
        "box": {
          "id": "remote-4",
          "maxclass": "newobj",
          "patching_rect": [
            105.0,
            413.0,
            165.0,
            22.0
          ],
          "text": "live.remote~ @normalized 1"
        }
      },
      {
        "box": {
          "id": "dial-4",
          "maxclass": "live.dial",
          "patching_rect": [
            300.0,
            413.0,
            48.0,
            42.0
          ],
          "parameter_enable": 0,
          "presentation": 1,
          "presentation_rect": [
            549.0,
            8.0,
            48.0,
            42.0
          ]
        }
      },
      {
        "box": {
          "id": "label-4",
          "maxclass": "comment",
          "patching_rect": [
            360.0,
            413.0,
            90.0,
            18.0
          ],
          "text": "MOTION",
          "presentation": 1,
          "presentation_rect": [
            545.0,
            51.0,
            62.0,
            16.0
          ]
        }
      },
      {
        "box": {
          "id": "led-4",
          "maxclass": "led",
          "patching_rect": [
            470.0,
            413.0,
            16.0,
            16.0
          ],
          "presentation": 1,
          "presentation_rect": [
            565.0,
            69.0,
            16.0,
            16.0
          ]
        }
      },
      {
        "box": {
          "id": "line-5",
          "maxclass": "newobj",
          "patching_rect": [
            25.0,
            465.0,
            60.0,
            22.0
          ],
          "text": "line~ 0."
        }
      },
      {
        "box": {
          "id": "remote-5",
          "maxclass": "newobj",
          "patching_rect": [
            105.0,
            465.0,
            165.0,
            22.0
          ],
          "text": "live.remote~ @normalized 1"
        }
      },
      {
        "box": {
          "id": "dial-5",
          "maxclass": "live.dial",
          "patching_rect": [
            300.0,
            465.0,
            48.0,
            42.0
          ],
          "parameter_enable": 0,
          "presentation": 1,
          "presentation_rect": [
            615.0,
            8.0,
            48.0,
            42.0
          ]
        }
      },
      {
        "box": {
          "id": "label-5",
          "maxclass": "comment",
          "patching_rect": [
            360.0,
            465.0,
            90.0,
            18.0
          ],
          "text": "DENSITY",
          "presentation": 1,
          "presentation_rect": [
            611.0,
            51.0,
            62.0,
            16.0
          ]
        }
      },
      {
        "box": {
          "id": "led-5",
          "maxclass": "led",
          "patching_rect": [
            470.0,
            465.0,
            16.0,
            16.0
          ],
          "presentation": 1,
          "presentation_rect": [
            631.0,
            69.0,
            16.0,
            16.0
          ]
        }
      }
    ],
    "lines": [
      {
        "patchline": {
          "source": [
            "audio-in",
            0
          ],
          "destination": [
            "audio-out",
            0
          ]
        }
      },
      {
        "patchline": {
          "source": [
            "audio-in",
            1
          ],
          "destination": [
            "audio-out",
            1
          ]
        }
      },
      {
        "patchline": {
          "source": [
            "rx",
            0
          ],
          "destination": [
            "engine",
            0
          ]
        }
      },
      {
        "patchline": {
          "source": [
            "load",
            0
          ],
          "destination": [
            "loadmsg",
            0
          ]
        }
      },
      {
        "patchline": {
          "source": [
            "loadmsg",
            0
          ],
          "destination": [
            "engine",
            0
          ]
        }
      },
      {
        "patchline": {
          "source": [
            "engine",
            12
          ],
          "destination": [
            "status",
            0
          ]
        }
      },
      {
        "patchline": {
          "source": [
            "engine",
            0
          ],
          "destination": [
            "line-0",
            0
          ]
        }
      },
      {
        "patchline": {
          "source": [
            "engine",
            0
          ],
          "destination": [
            "dial-0",
            0
          ]
        }
      },
      {
        "patchline": {
          "source": [
            "engine",
            1
          ],
          "destination": [
            "remote-0",
            1
          ]
        }
      },
      {
        "patchline": {
          "source": [
            "line-0",
            0
          ],
          "destination": [
            "remote-0",
            0
          ]
        }
      },
      {
        "patchline": {
          "source": [
            "remote-0",
            0
          ],
          "destination": [
            "led-0",
            0
          ]
        }
      },
      {
        "patchline": {
          "source": [
            "engine",
            2
          ],
          "destination": [
            "line-1",
            0
          ]
        }
      },
      {
        "patchline": {
          "source": [
            "engine",
            2
          ],
          "destination": [
            "dial-1",
            0
          ]
        }
      },
      {
        "patchline": {
          "source": [
            "engine",
            3
          ],
          "destination": [
            "remote-1",
            1
          ]
        }
      },
      {
        "patchline": {
          "source": [
            "line-1",
            0
          ],
          "destination": [
            "remote-1",
            0
          ]
        }
      },
      {
        "patchline": {
          "source": [
            "remote-1",
            0
          ],
          "destination": [
            "led-1",
            0
          ]
        }
      },
      {
        "patchline": {
          "source": [
            "engine",
            4
          ],
          "destination": [
            "line-2",
            0
          ]
        }
      },
      {
        "patchline": {
          "source": [
            "engine",
            4
          ],
          "destination": [
            "dial-2",
            0
          ]
        }
      },
      {
        "patchline": {
          "source": [
            "engine",
            5
          ],
          "destination": [
            "remote-2",
            1
          ]
        }
      },
      {
        "patchline": {
          "source": [
            "line-2",
            0
          ],
          "destination": [
            "remote-2",
            0
          ]
        }
      },
      {
        "patchline": {
          "source": [
            "remote-2",
            0
          ],
          "destination": [
            "led-2",
            0
          ]
        }
      },
      {
        "patchline": {
          "source": [
            "engine",
            6
          ],
          "destination": [
            "line-3",
            0
          ]
        }
      },
      {
        "patchline": {
          "source": [
            "engine",
            6
          ],
          "destination": [
            "dial-3",
            0
          ]
        }
      },
      {
        "patchline": {
          "source": [
            "engine",
            7
          ],
          "destination": [
            "remote-3",
            1
          ]
        }
      },
      {
        "patchline": {
          "source": [
            "line-3",
            0
          ],
          "destination": [
            "remote-3",
            0
          ]
        }
      },
      {
        "patchline": {
          "source": [
            "remote-3",
            0
          ],
          "destination": [
            "led-3",
            0
          ]
        }
      },
      {
        "patchline": {
          "source": [
            "engine",
            8
          ],
          "destination": [
            "line-4",
            0
          ]
        }
      },
      {
        "patchline": {
          "source": [
            "engine",
            8
          ],
          "destination": [
            "dial-4",
            0
          ]
        }
      },
      {
        "patchline": {
          "source": [
            "engine",
            9
          ],
          "destination": [
            "remote-4",
            1
          ]
        }
      },
      {
        "patchline": {
          "source": [
            "line-4",
            0
          ],
          "destination": [
            "remote-4",
            0
          ]
        }
      },
      {
        "patchline": {
          "source": [
            "remote-4",
            0
          ],
          "destination": [
            "led-4",
            0
          ]
        }
      },
      {
        "patchline": {
          "source": [
            "engine",
            10
          ],
          "destination": [
            "line-5",
            0
          ]
        }
      },
      {
        "patchline": {
          "source": [
            "engine",
            10
          ],
          "destination": [
            "dial-5",
            0
          ]
        }
      },
      {
        "patchline": {
          "source": [
            "engine",
            11
          ],
          "destination": [
            "remote-5",
            1
          ]
        }
      },
      {
        "patchline": {
          "source": [
            "line-5",
            0
          ],
          "destination": [
            "remote-5",
            0
          ]
        }
      },
      {
        "patchline": {
          "source": [
            "remote-5",
            0
          ],
          "destination": [
            "led-5",
            0
          ]
        }
      }
    ],
    "dependency_cache": [
      {
        "name": "mirror_hands.js",
        "bootpath": ".",
        "type": "TEXT",
        "implicit": 1
      }
    ],
    "latency": 0,
    "autosave": 0
  }
}
