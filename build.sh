#!/usr/bin/env bash
# Rebuild dist/SnipStudio.apk from web/index.html and android/.
# Works on macOS and Linux. Needs: curl, a JDK (java + javac, 11+), and uv (or python3 with `cryptography`).
set -euo pipefail

# Bump VERSION_CODE for every release you install over an older one.
VERSION_CODE="${VERSION_CODE:-1}"
VERSION_NAME="${VERSION_NAME:-1.0}"

ROOT="$(cd "$(dirname "$0")" && pwd)"
TOOLS="$ROOT/.tools"
BUILD="$ROOT/build"
DIST="$ROOT/dist"
# Keep the key outside git. Same key = updates install over the existing app.
KEY="${SNIP_SIGNING_KEY:-$ROOT/android/snip-studio-signing-key.pem}"
mkdir -p "$TOOLS" "$BUILD/asm" "$BUILD/assets" "$DIST"

# --- toolchain (downloaded once into .tools/) ---
fetch_npm() { # package version dest
  local tarball="https://registry.npmjs.org/$1/-/$(basename "$1")-$2.tgz"
  if [ ! -d "$3" ]; then
    echo "fetching $1@$2"
    mkdir -p "$3" && curl -fsSL "$tarball" | tar xz -C "$3"
  fi
}
fetch_npm aaptjs3 2.0.2 "$TOOLS/aaptjs3"        # prebuilt aapt2 (resource compiler)
fetch_npm apktool-jar 2.4.1 "$TOOLS/apktool-jar" # contains the smali assembler
if [ ! -f "$TOOLS/android-34.jar" ]; then
  echo "fetching android-34.jar"
  curl -fsSL -o "$TOOLS/android-34.jar" https://raw.githubusercontent.com/Sable/android-platforms/master/android-34/android.jar
fi

case "$(uname -s)" in
  Darwin) OS=darwin ;; # x64 binary; runs under Rosetta on Apple Silicon
  Linux) OS=linux ;;
  *) echo "unsupported OS: $(uname -s)" >&2; exit 1 ;;
esac
AAPT2="$TOOLS/aaptjs3/package/bin/x64/$OS/aapt2"
APKTOOL="$TOOLS/apktool-jar/package/bin/apktool_2.4.1.jar"
chmod +x "$AAPT2"

# --- resources + manifest ---
"$AAPT2" compile --dir "$ROOT/android/res" -o "$BUILD/res.zip"
"$AAPT2" link -o "$BUILD/base.apk" -I "$TOOLS/android-34.jar" \
  --manifest "$ROOT/android/AndroidManifest.xml" \
  --min-sdk-version 29 --target-sdk-version 34 \
  --version-code "$VERSION_CODE" --version-name "$VERSION_NAME" \
  "$BUILD/res.zip"

# --- native wrapper: smali -> classes.dex ---
javac -nowarn -cp "$APKTOOL" -d "$BUILD/asm" "$ROOT/android/tools-src/Asm.java"
java -cp "$BUILD/asm:$APKTOOL" Asm "$ROOT/android/smali" "$BUILD/classes.dex" 29

# --- package, align, sign ---
cp "$ROOT/web/index.html" "$BUILD/assets/index.html"
if command -v uv >/dev/null; then
  PY=(uv run --project "$ROOT" python)
else
  PY=(python3)
fi
"${PY[@]}" "$ROOT/android/pack_and_sign.py" "$BUILD/base.apk" "$BUILD/classes.dex" "$BUILD/assets" "$KEY" "$DIST/SnipStudio.apk"
