"""A floor-plan picture and the MAP config group for the dashboard's Map tab, drawn from a domain's `layout()` only.

Frames follow ROS map.yaml: origin = world (x, y) of the image's bottom-left corner, row 0 = top. Needs Pillow (the server extra).
"""
from __future__ import annotations

import io
import os

MAX_PX = 1600
MARGIN_M = 0.6
MARGIN_PX = 90
KIND_FILL = {"surface": (201, 183, 156), "container": (169, 184, 201), "seat": (212, 169, 169), "dock": (159, 209, 159),
             "bin": (190, 200, 170), "lane": (230, 190, 120)}
FONTS = ["/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
         "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"]


def _points(layout: dict):
    for r in layout.get("regions", []):
        yield (r["rect"][0], r["rect"][1])
        yield (r["rect"][2], r["rect"][3])
    for p in layout.get("places", []) + layout.get("labels", []):
        yield tuple(p["pos"])


def frame_for(layout: dict) -> dict | None:
    pts = list(_points(layout))
    if not pts:
        return None
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    raw = max(max(xs) - min(xs), max(ys) - min(ys), 1.0)
    ppm = min(100.0, (MAX_PX - 2 * MARGIN_PX) / raw)
    m = max(MARGIN_M, MARGIN_PX / ppm)                      # room for the labels of the outermost places
    x0, y0 = min(xs) - m, min(ys) - m
    w, h = max(xs) + m - x0, max(ys) + m - y0
    return {"resolution": round(1.0 / ppm, 6), "origin": [round(x0, 3), round(y0, 3)], "width": int(round(w * ppm)), "height": int(round(h * ppm)),
            "_ppm": ppm}


def _font(size: int):
    from PIL import ImageFont
    for path in FONTS:
        if os.path.exists(path):
            return ImageFont.truetype(path, size, index=1) if path.endswith(".ttc") else ImageFont.truetype(path, size)
    return ImageFont.load_default()


def render_png(layout: dict) -> tuple:
    """-> (png bytes, frame) or (None, None) when the layout has nothing to draw."""
    from PIL import Image, ImageDraw
    f = frame_for(layout)
    if f is None:
        return None, None
    ppm = f.pop("_ppm")
    px = lambda x, y: ((x - f["origin"][0]) * ppm, f["height"] - (y - f["origin"][1]) * ppm)    # noqa: E731
    img = Image.new("RGB", (f["width"], f["height"]), (251, 251, 251))
    d = ImageDraw.Draw(img)
    big, small = _font(22), _font(16)
    for r in layout.get("regions", []):
        (ax, ay), (bx, by) = px(r["rect"][0], r["rect"][3]), px(r["rect"][2], r["rect"][1])
        d.rectangle([ax, ay, bx, by], fill=(240, 240, 236), outline=(85, 85, 85), width=5)
        d.text((ax + 10, ay + 8), str(r["name"]), fill=(110, 110, 110), font=big)
    for dr in layout.get("doors", []):
        cx, cy = px(*dr["at"])
        half = dr["width"] * ppm / 2
        vertical = any(abs(dr["at"][0] - v) < 1e-6 for r in layout.get("regions", []) for v in (r["rect"][0], r["rect"][2]))
        dx, dy = (7, half) if vertical else (half, 7)
        d.rectangle([cx - dx, cy - dy, cx + dx, cy + dy], fill=(251, 251, 251))
    for lb in layout.get("labels", []):
        x, y = px(*lb["pos"])
        d.text((x, y), str(lb["text"]), fill=(150, 150, 150), font=big)
    for p in layout.get("places", []):
        x, y = px(*p["pos"])
        d.rounded_rectangle([x - 14, y - 14, x + 14, y + 14], radius=5, fill=KIND_FILL.get(p.get("kind"), (221, 221, 221)), outline=(68, 68, 68), width=2)
        w = d.textlength(str(p["name"]), font=small)
        d.text((x - w / 2, y + 18), str(p["name"]), fill=(51, 51, 51), font=small)
    buf = io.BytesIO()
    img.save(buf, "PNG")
    return buf.getvalue(), f


def map_config(frame: dict, file: str = "map/map.png", goal_skill: str = "move_to") -> dict:
    """The MAP group the dashboard reads: picture + pose + click-to-move + the Sim bar's agent."""
    return {"image": {"file": file, "frame": frame}, "places": "ENV",
            "pose": {"agent": "mobile_pose", "x": "x", "y": "y", "yaw": "yaw", "angle": "rad", "period_s": 0.5},
            "goal": {"skill": goal_skill, "params": {"x": "{x}", "y": "{y}"}},
            "confirm_goal": False, "sim": {"agent": "sim_command"}}
