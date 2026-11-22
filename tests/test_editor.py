"""Browser smoke tests for web/index.html.

Run with:  uv run playwright install chromium  (once)  then  uv run pytest
"""

from collections.abc import Iterator
from dataclasses import dataclass, field
from pathlib import Path

import pytest
from PIL import Image, ImageDraw
from playwright.sync_api import Page, sync_playwright

EDITOR = Path(__file__).resolve().parents[1] / "web" / "index.html"
Point = tuple[float, float]


@dataclass
class Editor:
    """Thin helper around a Page: converts document coordinates to screen and drives gestures."""

    page: Page
    errors: list[str] = field(default_factory=list)

    def js(self, expr: str):
        return self.page.evaluate(expr)

    def to_screen(self, x: float, y: float) -> Point:
        box = self.page.eval_on_selector("#cv", "e => { const r = e.getBoundingClientRect(); return [r.x, r.y]; }")
        v = self.js("({z: view.z, x: view.x, y: view.y})")
        return box[0] + x * v["z"] + v["x"], box[1] + y * v["z"] + v["y"]

    def drag(self, *path: Point) -> None:
        """Press at the first document point, move through the rest, release."""
        mouse = self.page.mouse
        mouse.move(*self.to_screen(*path[0]))
        mouse.down()
        for pt in path[1:]:
            mouse.move(*self.to_screen(*pt), steps=6)
        mouse.up()

    def tap(self, selector: str) -> None:
        self.page.click(selector)


@pytest.fixture(scope="session")
def photo(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """A 1200x900 test photo: gradient background, yellow circle, red rectangle."""
    img = Image.new("RGB", (1200, 900))
    draw = ImageDraw.Draw(img)
    for y in range(900):
        draw.line([(0, y), (1200, y)], fill=(40 + y // 6, 90 + y // 10, 160))
    draw.ellipse([200, 200, 500, 500], fill=(255, 200, 0))
    draw.rectangle([700, 300, 1000, 700], fill=(220, 40, 60))
    path = tmp_path_factory.mktemp("img") / "photo.jpg"
    img.save(path, quality=90)
    return path


@pytest.fixture
def editor(photo: Path, request: pytest.FixtureRequest) -> Iterator[Editor]:
    init_script: str | None = getattr(request, "param", None)
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 400, "height": 820}, device_scale_factor=2)
        ed = Editor(page)
        page.on("pageerror", lambda e: ed.errors.append(str(e)))
        if init_script:
            page.add_init_script(init_script)
        page.goto(EDITOR.as_uri())
        page.set_input_files("#file", str(photo))
        page.wait_for_function("doc !== null")
        yield ed
        browser.close()
    assert ed.errors == [], f"page errors: {ed.errors}"


def test_open_photo_sets_canvas_to_photo_size(editor: Editor) -> None:
    assert editor.js("doc") == {"w": 1200, "h": 900, "bg": "transparent"}
    assert editor.js("layers.length") == 1
    assert editor.page.is_hidden("#welcome")


def test_dragging_inside_selection_lifts_it_into_a_new_layer(editor: Editor) -> None:
    editor.tap("[data-tool=select]")
    editor.drag((180, 180), (350, 350), (520, 520))
    assert editor.js("sel !== null")
    editor.drag((350, 350), (800, 450))
    state = editor.js("({tool, names: layers.map(l => l.name), x: Math.round(active().x)})")
    assert state["tool"] == "move"
    assert state["names"][-1] == "Cut piece"
    assert state["x"] == 800


def test_lasso_cut_takes_every_visible_layer_then_paste(editor: Editor) -> None:
    editor.tap("[data-tool=select]")
    editor.drag((180, 180), (520, 520))
    editor.drag((350, 350), (800, 450))  # circle now overlaps the red rectangle
    editor.tap("[data-tool=lasso]")
    editor.drag((650, 250), (1050, 250), (1050, 750), (650, 750), (650, 250))
    editor.tap('#ctx .act:has-text("Cut")')
    editor.tap('#ctx .act:has-text("Paste")')
    names = editor.js("layers.map(l => l.name)")
    assert names == ["photo", "Cut piece", "Pasted"]
    # the pasted piece is a composite of both layers, so it covers the whole lasso box
    assert editor.js("[active().canvas.width, active().canvas.height]") == [400, 500]


def test_undo_restores_previous_state(editor: Editor) -> None:
    editor.tap("[data-tool=select]")
    editor.drag((180, 180), (520, 520))
    editor.drag((350, 350), (800, 450))
    assert editor.js("layers.length") == 2
    editor.tap("#bUndo")
    assert editor.js("layers.length") == 1
    editor.tap("#bRedo")
    assert editor.js("layers.length") == 2


def test_crop_to_square(editor: Editor) -> None:
    editor.tap("[data-tool=crop]")
    editor.tap('#ctx .act:has-text("1:1")')
    editor.tap('#ctx .act:has-text("Apply")')
    assert editor.js("[doc.w, doc.h]") == [900, 900]


def test_two_finger_pinch_zooms_the_view(editor: Editor) -> None:
    before = editor.js("view.z")
    editor.js(
        """() => {
        const cv = document.querySelector('#cv'), r = cv.getBoundingClientRect();
        const ev = (t, id, x, y) => cv.dispatchEvent(new PointerEvent(t, {pointerId: id, clientX: r.left + x,
            clientY: r.top + y, pointerType: 'touch', bubbles: true, isPrimary: id === 1}));
        ev('pointerdown', 1, 150, 60); ev('pointerdown', 2, 250, 60);
        for (let i = 1; i <= 10; i++) { ev('pointermove', 1, 150 - i * 8, 60); ev('pointermove', 2, 250 + i * 8, 60); }
        ev('pointerup', 1, 70, 60); ev('pointerup', 2, 330, 60);
    }"""
    )
    assert editor.js("view.z") == pytest.approx(before * 2.6, rel=0.05)


def test_zoomed_out_layers_draw_from_cached_half_size_copies(editor: Editor) -> None:
    sizes = editor.js("""() => {
        const c = layers[0].canvas, a = proxyFor(c, 0.1), b = proxyFor(c, 0.1);
        return {same: a === b, full: proxyFor(c, 0.8) === c, w: a.width, src: c.width};
    }""")
    assert sizes["same"] and sizes["full"]
    assert sizes["w"] == sizes["src"] // 8  # 0.1 needs >= 1 source px per device px: 1/8 size


def test_tapping_transparent_part_of_a_cut_out_does_not_grab_it(editor: Editor) -> None:
    editor.tap("[data-tool=lasso]")
    editor.drag((350, 180), (520, 350), (350, 520), (180, 350), (350, 180))  # diamond around the circle
    editor.tap('#ctx .act:has-text("To layer")')
    assert editor.js("active().name") == "Cut piece"
    # the diamond's bounding-box corner is transparent in the cut piece, so the photo underneath gets picked
    assert editor.js("pick(190, 190).name") == "photo"
    assert editor.js("pick(350, 350).name") == "Cut piece"


ANDROID_MOCK = "window.AndroidBridge = {saveImage: (b, n, m) => { window._saved = [b.length, n, m]; return 'ok'; }};"


@pytest.mark.parametrize("editor", [ANDROID_MOCK], indirect=True)
def test_android_save_goes_through_native_bridge(editor: Editor) -> None:
    editor.tap("#bSave")
    editor.tap("#sJpg")
    editor.page.wait_for_function("window._saved")
    size, name, mime = editor.js("window._saved")
    assert size > 1000 and name.endswith(".jpg") and mime == "image/jpeg"


def test_android_back_closes_menu_before_leaving(editor: Editor) -> None:
    editor.tap("#bMenu")
    assert editor.js("androidBack()") is True
    assert editor.page.is_hidden("#menu")
    assert editor.js("androidBack()") is False
