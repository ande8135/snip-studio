# Snip Studio

A touch-first photo editor (cut, crop, rearrange, save; think a pocket MS Paint with layers). One self-contained
web page, shipped two ways:

1. **Android app**: `dist/SnipStudio.apk`, a thin native WebView wrapper around the page. This is the main target.
2. **Claude artifact**: the same page published at https://claude.ai/artifact/JC5UCJWnowqCzVnBeqtTMg
   (slug `8b374af0-8df0-489e-bd44-038ca7ed0c6f`), using the artifact `downloads` capability for saving.

Built in a claude.ai conversation (Nov 2026) and moved here so work can continue in Claude Code.

## Layout

```
web/index.html            the whole editor: HTML + CSS + JS, no build step, no dependencies
android/AndroidManifest.xml
android/res/              theme + adaptive launcher icon
android/smali/            native wrapper, hand-written smali (4 small classes, see below)
android/tools-src/        Asm.java (drives the smali assembler), Dump.java (lists classes/methods in a dex)
android/pack_and_sign.py  zip-aligns the APK and signs it with APK Signature Scheme v2 (own code, `cryptography`)
build.sh                  one-shot build: fetches toolchain into .tools/, writes dist/SnipStudio.apk
tests/test_editor.py      Playwright smoke tests against web/index.html (pytest)
```

## Commands

```sh
./build.sh                                   # -> dist/SnipStudio.apk
VERSION_CODE=2 VERSION_NAME=1.1 ./build.sh   # bump for a release that installs over the old one
uv run playwright install chromium           # once
uv run pytest                                # browser tests
uvx ruff check . && uvx ruff format .        # lint/format Python
open web/index.html                          # the editor runs straight from disk in any browser
```

Install on the phone: send the APK over (or `adb install -r dist/SnipStudio.apk`) and allow the unknown-sources prompt.

## Signing key (important)

`android/snip-studio-signing-key.pem` (PEM: PKCS#8 RSA-2048 key + self-signed cert, SHA-256 of cert starts
`77e21e6adb947566`). It is gitignored and must never be committed. The owner has a copy. Builds signed with any other
key will not install over the existing app (uninstall first). Override the location with `SNIP_SIGNING_KEY=/path`.
If the file is missing, `pack_and_sign.py` silently generates a new key, so check for it before building a release.

## Why the Android build is unusual

The project was created in a cloud sandbox where Google's SDK/Maven hosts were blocked, so there is no Gradle and no
Android SDK. Instead:

- `aapt2` comes from the npm package `aaptjs3` (prebuilt binaries for linux/darwin x64).
- `android.jar` (API 34) comes from github.com/Sable/android-platforms via raw.githubusercontent.com.
- Java can't be compiled to dex (no d8 available), so the native code is written directly in **smali** and assembled
  with the smali assembler inside the npm package `apktool-jar` (apktool 2.4.1). Its CLI entry point is stripped, so
  `Asm.java` calls `brut.androlib.src.SmaliBuilder.build(...)` instead.
- No `apksigner`/`zipalign`: `pack_and_sign.py` stores `resources.arsc` and PNGs uncompressed and 4-byte aligned
  (required for targetSdk 30+) and writes a v2 signature block (v2 alone is valid because minSdk is 29). It
  re-verifies its own signature and alignment after writing.

On a Mac with Android Studio this could be replaced by a conventional Gradle project with a Java/Kotlin
`MainActivity`. That is a reasonable future move if the native side grows; keep behaviour identical to the smali.
Neither the smali nor the APK has been run through Google's verifier/`apksigner verify`; if a real SDK becomes
available, run `apksigner verify --verbose dist/SnipStudio.apk` as a check.

## Native wrapper (android/smali/com/snipstudio/editor)

- `MainActivity`: full-screen `WebView` loading `file:///android_asset/index.html` (JS + DOM storage on). Adds the JS
  interface `AndroidBridge`. `onActivityResult` feeds picked image URIs (single or multiple via `ClipData`) back to
  the pending file chooser. `onBackPressed` evaluates `window.androidBack()`; if that returns false the task is moved
  to the background (not finished) so unsaved work survives.
- `Chrome` (`WebChromeClient`): `onShowFileChooser` launches `FileChooserParams.createIntent()` with
  `EXTRA_ALLOW_MULTIPLE` when the input has `multiple`.
- `Bridge`: `@JavascriptInterface saveImage(base64, filename, mime) -> "ok" | error text`. Writes via MediaStore to
  `Pictures/Snip Studio` (needs API 29+, no storage permission).
- `BackCb`: `ValueCallback` for the back-button JS result.

Manifest: `configChanges` covers rotation/size/uiMode so the activity is never recreated (that would wipe the
editor). minSdk 29, targetSdk 34 (35 would force edge-to-edge and need inset handling in the page).

When editing smali: `.registers N` = locals + params (params occupy the last registers, `p0` = `this`); keep the
register types consistent at every branch target and exception handler. After assembling, `Dump.java` prints each
method's register count, instruction count and try blocks as a quick sanity check.

## Editor architecture (web/index.html)

Plain JS, single `<script>`, no framework. Key state (all top-level `let`s, which the tests read directly):

- `doc = {w, h, bg}`: canvas size and background (`'transparent'` or a colour). `null` until something is opened.
- `layers` (bottom to top): `{id, name, canvas, x, y, s, r, fx, fy, visible, opacity}`. Each layer is a bitmap
  (`<canvas>`) plus a transform: centre `(x, y)` in document px, uniform scale `s`, rotation `r` (radians), flips.
  `LM(layer)` builds the local-to-document `DOMMatrix`; `VM()` is document-to-screen (includes devicePixelRatio).
- `view = {z, x, y}`: zoom and pan. `s2d`/`d2s` convert between screen CSS px and document px.
- `sel = {kind, pts}`: selection polygon in document coords (rectangles are 4-point polygons).
- `clip`: internal clipboard (a canvas plus the transform it came from).

**Undo model**: layer bitmaps are treated as immutable; any pixel edit replaces `layer.canvas` with a new canvas.
So a history snapshot is just shallow copies of the layer objects (`snap()`), which is cheap. Call `checkpoint()`
*before* mutating; `HIST = 30` steps. Drags checkpoint on first movement; a second finger landing mid-gesture rolls
the first gesture back (`cancelSingle`).

**Selections** (`grab()`): by default cut/copy takes *everything visible* inside the selection, Paint-style (`selFrom
= 'all'`); the toolbar toggle switches to the active layer only. With one source layer the pixels are extracted
exactly in that layer's own space; with several, they are composited at the finest source resolution.
Dragging inside a selection lifts it into a new layer (`doLift`).

**Input**: Pointer Events. One finger runs the current tool; two fingers pinch-zoom the view, or (Move tool, starting
on the active layer) scale and rotate that layer. Move tool: corner handles scale, the knob rotates (snaps to 90°),
tap on empty space pans or deselects. Hit-testing uses pixel alpha so transparent parts of cut-outs don't grab.

**Saving** (`save(fmt)`), in order: `window.AndroidBridge` (APK) → artifact `downloads` capability via
`window.claude.use('downloads')` → fallback preview modal (long-press to save, plus an `<a download>`).
`window.androidBack()` closes the modal, menu or sheet, clears the selection, or leaves crop; returns false when
nothing is open.

Limits: images are downscaled to `MAXDIM = 4096` on import; the artifact sandbox blocks direct downloads, service
workers and Web Share (hence the capability).

## Updating the artifact

The artifact is updated from claude.ai (the Artifact tools aren't available in Claude Code). In a claude.ai
conversation, publish `web/index.html` to the slug above; keep the `downloads` capability declared.

## Status and ideas

- Working: open/add photos, rectangle and lasso select, cut/copy/paste/lift/erase, crop with aspect presets,
  move/scale/rotate/flip, layer reorder/visibility/opacity/merge/flatten, brush and eraser, resize, rotate/flip image,
  background colour, undo/redo, PNG/JPG save.
- The APK passed structural checks (signature, alignment, dex checksums) and the page passed the browser tests, but
  the APK has not been run in an emulator; ask the owner how it behaves on their phone.
- iPhone: no sideloading in the US. Options are a home-screen web app (host `web/index.html` on GitHub Pages and add
  a manifest + Web Share for saving to Photos) or a WKWebView wrapper built in Xcode (free Apple ID = 7-day expiry,
  $99/yr developer program = 1 year/TestFlight).
- Possible features: text tool, shapes, magic-wand select, feathered edges, autosave to IndexedDB, share sheet.

## Conventions

- Keep `web/index.html` dependency-free and self-contained (it is copied verbatim into the APK and the artifact).
- Python: 3.13+, uv for everything, type hints, Ruff (line length 120), pytest.
- Add or extend a test in `tests/test_editor.py` for editor behaviour changes.
