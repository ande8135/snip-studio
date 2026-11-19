# Snip Studio

A photo editor for your phone: cut, crop, rearrange, draw and save. A bit like MS Paint with layers.

- **Android:** run `./build.sh`, then install `dist/SnipStudio.apk` on the phone (Android 10+).
- **Any browser:** open `web/index.html`. The whole editor is that one file.

## Using it

| Tool | What it does |
| --- | --- |
| Move | Tap a piece to select it. Drag to move it, pull a corner to resize, use the knob to rotate. Pinch on a piece to scale and rotate it. |
| Select / Lasso | Box or freehand selection, then Cut, Copy, To layer, Erase or Crop. Drag inside a selection to pull it out. |
| Crop | Free crop or a preset shape (1:1, 4:3, 16:9…). Drag the handles past the edge to make the canvas bigger. |
| Brush / Eraser | Draw on the selected layer (or a new one). |

Pinch with two fingers to zoom. The layers button opens reorder, visibility, opacity, merge and delete. In the app,
Save writes to **Pictures › Snip Studio**.

## Building

Needs `curl`, a JDK (`java` and `javac`) and [uv](https://docs.astral.sh/uv/). `build.sh` downloads the rest
(aapt2, the smali assembler and `android.jar`) into `.tools/` the first time it runs. See `CLAUDE.md` for why the
build works this way and how the native wrapper is put together.

Put the signing key at `android/snip-studio-signing-key.pem` (it's gitignored), or set `SNIP_SIGNING_KEY`. Updates
only install over the existing app if they're signed with the same key.

## Tests

```sh
uv run playwright install chromium
uv run pytest
```
