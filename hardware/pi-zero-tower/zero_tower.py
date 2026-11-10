# /// script
# requires-python = ">=3.10"
# dependencies = ["manifold3d>=3.0", "numpy", "matplotlib"]
# ///
"""
pokedesk Pi Zero tower: a stackable, 3D-printable case for Raspberry Pi Zero / Zero W / Zero 2 W.

Each Pi sits in its own identical tray. You print N trays and one lid. Four M3 screws run
through the corner columns, from the lid down into nuts trapped in the bottom tray, and
clamp the stack together. Each tray has a cut-out for the PWR micro-USB plug on the
port-side wall, so a short cable from every Pi runs out to a USB hub next to the tower.

    uv run zero_tower.py              # writes stl/*.stl + preview.png
    uv run zero_tower.py --pis 3      # override the stack count

Coordinate convention (matches the official Pi Zero mechanical drawing):
  X = along the 65 mm edge, the micro-SD card is at X=0
  Y = along the 30 mm edge, the ports (mini-HDMI / USB / PWR) are at Y=0, GPIO at Y=30
"""
from __future__ import annotations

import argparse
import math
import struct
from pathlib import Path

import numpy as np
from manifold3d import CrossSection, FillRule, JoinType, Manifold, set_circular_segments

set_circular_segments(48)

# ---------------------------------------------------------------- parameters
P = dict(
    pis=4,                 # trays in the stack
    # Pi Zero board (official drawing)
    pcb_w=65.0, pcb_d=30.0, pcb_t=1.4,
    holes=[(3.5, 3.5), (61.5, 3.5), (3.5, 26.5), (61.5, 26.5)],
    port_hdmi_x=12.4, port_usb_x=41.4, port_pwr_x=54.0,
    sd_center_y=16.9, cam_center_y=15.0,
    # which wall openings to cut
    open_pwr=True,         # always: the power cable
    open_usb=False,        # data/OTG port (needed for USB-gadget networking through the hub)
    open_hdmi=False,       # mini-HDMI (only for debugging)
    # what is above the board
    gpio_header=False,     # soldered 2x20 header? (raises the tray)
    heatsink_h=5.0,        # stick-on heatsink height (recommended on a Zero 2 W); 0 if none
    # case
    clr=1.0,               # gap between PCB edge and inner wall
    wall=2.0,
    floor=1.6,
    # Pi mounting posts take M2.5 brass heat-set inserts (common M2.5 x 4 mm long x 3.5 mm OD).
    # Check your insert's datasheet for the recommended hole and adjust insert_hole_d.
    standoff_h=4.0,        # tall enough that the insert sits fully inside the post
    standoff_d=6.5,        # leaves ~1.6 mm of plastic around the insert
    insert_hole_d=3.2, insert_len=4.0,
    insert_extra=1.0,      # depth below the insert for displaced plastic and the screw tip
    top_gap=1.5,           # air above the tallest part
    # micro-USB plug overmold opening (fits most straight and 90° plugs)
    plug_w=12.0, plug_h=8.5, plug_zc=1.4,   # plug_zc = port centre above the PCB top
    hdmi_w=13.0, hdmi_h=8.5,
    # M3 clamp columns
    col_r=3.6, bolt_d=3.4, nut_af=5.7, nut_t=2.4,   # M3 hex nut: 5.5 AF, 2.4 thick
    lid_t=2.4,
    # two-colour print (multi-material printer): each part is exported as a white body + black body
    band_h=3.0,            # black base band on every tray: a black line between Pis once stacked
    lid_text="pokedesk",   # black inlay on the lid top
    text_h=6.0, text_depth=0.6,   # text height (ascender to descender) and inlay depth (3 layers @ 0.2)
    corner_r=2.5,
)


# ---------------------------------------------------------------- helpers
def box(x0, y0, z0, x1, y1, z1) -> Manifold:
    return Manifold.cube([x1 - x0, y1 - y0, z1 - z0]).translate([x0, y0, z0])


def rbox(x0, y0, z0, x1, y1, z1, r) -> Manifold:
    """Box rounded on its vertical edges."""
    cs = CrossSection.square([x1 - x0 - 2 * r, y1 - y0 - 2 * r]).translate([r, r])
    cs = cs.offset(r, JoinType.Round)
    return cs.extrude(z1 - z0).translate([x0, y0, z0])


def cyl(x, y, z0, h, d) -> Manifold:
    return Manifold.cylinder(h, d / 2).translate([x, y, z0])


def hexagon(x, y, z0, h, af) -> Manifold:
    return Manifold.cylinder(h, af / 2 / math.cos(math.pi / 6), circular_segments=6).translate([x, y, z0])


def slot_x(x0, x1, y, z0, h, w) -> Manifold:
    """Stadium-shaped slot running along X (cuts through anything in Z)."""
    cs = CrossSection.square([x1 - x0, 0.001]).translate([x0, y]).offset(w / 2, JoinType.Round)
    return cs.extrude(h).translate([0, 0, z0])


def wall_hole_y(xc, zc, w, h, y0, y1, r=1.5) -> Manifold:
    """Rounded rectangular hole through a wall that is normal to Y."""
    cs = CrossSection.square([w - 2 * r, h - 2 * r]).translate([xc - w / 2 + r, zc - h / 2 + r]).offset(r, JoinType.Round)
    # extrude along Z then rotate so the extrusion is along +Y
    return cs.extrude(y1 - y0).rotate([90, 0, 0]).translate([0, y1, 0])


def wall_hole_x(yc, zc, w, h, x0, x1, r=1.5) -> Manifold:
    cs = CrossSection.square([w - 2 * r, h - 2 * r]).translate([yc - w / 2 + r, zc - h / 2 + r]).offset(r, JoinType.Round)
    return cs.extrude(x1 - x0).rotate([90, 0, 90]).translate([x0, 0, 0])


# ---------------------------------------------------------------- derived dims
def dims(p):
    d = {}
    d["cav_x0"] = p["wall"]
    d["cav_y0"] = p["wall"]
    d["cav_w"] = p["pcb_w"] + 2 * p["clr"]
    d["cav_d"] = p["pcb_d"] + 2 * p["clr"]
    d["out_w"] = d["cav_w"] + 2 * p["wall"]
    d["out_d"] = d["cav_d"] + 2 * p["wall"]
    d["pcb_x0"] = d["cav_x0"] + p["clr"]
    d["pcb_y0"] = d["cav_y0"] + p["clr"]
    d["pcb_bot"] = p["floor"] + p["standoff_h"]
    d["pcb_top"] = d["pcb_bot"] + p["pcb_t"]
    above = max(3.3,                         # USB / HDMI receptacles
                p["heatsink_h"] + 1.2,       # SoC + heatsink
                8.6 if p["gpio_header"] else 0)
    # Tray height is rounded UP to a multiple of 5 mm. Then the clamp screw is always exactly
    # pis x pitch long (a standard M3 length), the screw tip always ends lid_t above the bed,
    # and the nut pocket depth never depends on the stack size. So trays printed today still
    # fit a taller tower later: print another tray, buy longer screws.
    need = d["pcb_top"] + above + p["top_gap"]
    d["pitch"] = math.ceil(need / 5.0 - 1e-9) * 5.0
    d["stack_h"] = p["pis"] * d["pitch"] + p["lid_t"]
    d["screw_l"] = int(p["pis"] * d["pitch"])
    # screw tension pulls the nut up against the pocket roof; the tip ends flush with its underside
    d["nut_pocket"] = p["lid_t"] + p["nut_t"] + 0.2
    assert d["nut_pocket"] < d["pitch"] - 3
    # clamp columns sit diagonally outside each cavity corner
    o = 1.9
    d["cols"] = [(d["cav_x0"] - o, d["cav_y0"] - o),
                 (d["cav_x0"] + d["cav_w"] + o, d["cav_y0"] - o),
                 (d["cav_x0"] - o, d["cav_y0"] + d["cav_d"] + o),
                 (d["cav_x0"] + d["cav_w"] + o, d["cav_y0"] + d["cav_d"] + o)]
    return d


def outline(p, d, z0, h) -> Manifold:
    shell = rbox(0, 0, z0, d["out_w"], d["out_d"], z0 + h, p["corner_r"])
    for (x, y) in d["cols"]:
        shell += cyl(x, y, z0, h, 2 * p["col_r"])
    return shell


# ---------------------------------------------------------------- tray
def tray(p) -> Manifold:
    d = dims(p)
    H = d["pitch"]
    body = outline(p, d, 0, H)
    # hollow it out
    body -= rbox(d["cav_x0"], d["cav_y0"], p["floor"], d["cav_x0"] + d["cav_w"], d["cav_y0"] + d["cav_d"], H + 1, 1.0)

    # standoffs for the Pi's mounting holes
    for hx, hy in p["holes"]:
        x, y = d["pcb_x0"] + hx, d["pcb_y0"] + hy
        body += cyl(x, y, p["floor"] - 0.01, p["standoff_h"] + 0.01, p["standoff_d"])
        top = p["floor"] + p["standoff_h"]
        hole_d = p["insert_hole_d"]
        depth = p["insert_len"] + p["insert_extra"]
        assert top - depth >= 0.5, "insert hole would break through the floor; raise standoff_h"
        body -= cyl(x, y, top - depth, depth + 1, hole_d)
        # 0.5 mm lead-in chamfer so the insert starts straight
        body -= Manifold.cylinder(0.5, hole_d / 2, hole_d / 2 + 0.5).translate([x, y, top - 0.5])

    # floor vents (chimney: warm air rises through every tray and out of the lid)
    vy0, vy1 = d["pcb_y0"] + 7.5, d["pcb_y0"] + p["pcb_d"] - 7.5
    for i in range(9):
        x = d["pcb_x0"] + 12 + i * 5.2
        body -= box(x - 1.1, vy0, -1, x + 1.1, vy1, p["floor"] + 1)
    for hy in (7.5, p["pcb_d"] - 7.5):   # extra slots between the standoffs
        body -= slot_x(d["pcb_x0"] + 10, d["pcb_x0"] + p["pcb_w"] - 10, d["pcb_y0"] + hy - 3.2, -1, p["floor"] + 2, 2.2)

    # port-side wall (Y=0): plug openings
    zc = d["pcb_top"] + p["plug_zc"]
    cut_y0, cut_y1 = -1, d["cav_y0"] + 0.5
    if p["open_pwr"] and p["open_usb"]:
        # two openings would leave a 0.6 mm web, so cut one wide one instead
        xa, xb = p["port_usb_x"], p["port_pwr_x"]
        xc = d["pcb_x0"] + (xa + xb) / 2
        body -= wall_hole_y(xc, zc, (xb - xa) + p["plug_w"], p["plug_h"], cut_y0, cut_y1)
    else:
        for on, px in ((p["open_pwr"], p["port_pwr_x"]), (p["open_usb"], p["port_usb_x"])):
            if on:
                body -= wall_hole_y(d["pcb_x0"] + px, zc, p["plug_w"], p["plug_h"], cut_y0, cut_y1)
    if p["open_hdmi"]:
        body -= wall_hole_y(d["pcb_x0"] + p["port_hdmi_x"], zc, p["hdmi_w"], p["hdmi_h"], cut_y0, cut_y1)

    # SD-card end (X=0): finger notch so the card can be pulled with the board in place
    sd_y = d["pcb_y0"] + p["sd_center_y"]
    body -= box(-1, sd_y - 7.5, p["floor"] + 1.0, d["cav_x0"] + 0.5, sd_y + 7.5, H + 1)

    # camera end (X=max): CSI ribbon slot (also an air inlet)
    cam_y = d["pcb_y0"] + p["cam_center_y"]
    body -= wall_hole_x(cam_y, d["pcb_top"] + 1.5, 19.0, 4.5, d["cav_x0"] + d["cav_w"] - 0.5, d["out_w"] + 1, r=1.0)

    # GPIO side (Y=max): vent slots, kept clear of the clamp columns
    for i in range(8):
        x = d["pcb_x0"] + 9 + i * 6.6
        body -= wall_hole_y(x, (p["floor"] + H) / 2 + 0.5, 2.4, H - p["floor"] - 4.0,
                            d["cav_y0"] + d["cav_d"] - 0.5, d["out_d"] + 1, r=1.1)

    # clamp-screw bores + hex-nut traps on the underside of every column (all trays are identical)
    for (x, y) in d["cols"]:
        body -= cyl(x, y, -1, H + 2, p["bolt_d"])
        body -= hexagon(x, y, -0.01, d["nut_pocket"], p["nut_af"] + 0.3)

    return body


# ---------------------------------------------------------------- lid
def lid(p) -> Manifold:
    d = dims(p)
    t = p["lid_t"]
    body = outline(p, d, 0, t)
    # vent grid over the SoC side of the board
    for i in range(10):
        x = d["pcb_x0"] + 8 + i * 5.2
        body -= box(x - 1.1, d["pcb_y0"] + 4, -1, x + 1.1, d["pcb_y0"] + 19, t + 1)
    for (x, y) in d["cols"]:
        body -= cyl(x, y, -1, t + 2, p["bolt_d"])
    # shallow locating rim that drops into the top tray's cavity
    rim_in = rbox(d["cav_x0"] + 0.25, d["cav_y0"] + 0.25, -1.2, d["cav_x0"] + d["cav_w"] - 0.25, d["cav_y0"] + d["cav_d"] - 0.25, 0.01, 0.8)
    rim_hole = rbox(d["cav_x0"] + 1.45, d["cav_y0"] + 1.45, -2, d["cav_x0"] + d["cav_w"] - 1.45, d["cav_y0"] + d["cav_d"] - 1.45, 1, 0.5)
    body += rim_in - rim_hole
    return body


# ---------------------------------------------------------------- two-colour split
def text_prism(p, d, z0, h) -> Manifold:
    from matplotlib.font_manager import FontProperties
    from matplotlib.textpath import TextPath
    tp = TextPath((0, 0), p["lid_text"], size=10, prop=FontProperties(family="DejaVu Sans", weight="bold"))
    cs = CrossSection([np.asarray(q, dtype=float) for q in tp.to_polygons()], FillRule.EvenOdd)
    (x0, y0), (x1, y1) = cs.bounds()[:2], cs.bounds()[2:]
    k = p["text_h"] / (y1 - y0)
    # in the strip between the vents and the GPIO-side edge, reading from that side (the front:
    # the cables leave from the port side, which faces the hub / the back)
    cx, cy = d["out_w"] / 2, (d["pcb_y0"] + 19 + d["out_d"]) / 2
    cs = cs.translate([-(x0 + x1) / 2, -(y0 + y1) / 2]).scale([k, k]).rotate(180).translate([cx, cy])
    return cs.extrude(h).translate([0, 0, z0])


def split_tray(p, T):
    band = box(-20, -20, -1, 200, 200, p["band_h"])
    return T - band, T ^ band          # white, black


def split_lid(p, d, L):
    t = p["lid_t"]
    ink = text_prism(p, d, t - p["text_depth"], p["text_depth"] + 1)
    return L - ink, L ^ ink            # white, black


# ---------------------------------------------------------------- output
def write_stl(m: Manifold, path: Path):
    mesh = m.to_mesh()
    v = np.asarray(mesh.vert_properties)[:, :3].astype(np.float32)
    t = np.asarray(mesh.tri_verts)
    tri = v[t]
    n = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
    n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)
    with open(path, "wb") as f:
        f.write(b"pokedesk pi-zero tower".ljust(80, b" "))
        f.write(struct.pack("<I", len(t)))
        rec = np.zeros(len(t), dtype=[("n", "<f4", 3), ("v", "<f4", (3, 3)), ("a", "<u2")])
        rec["n"], rec["v"] = n, tri
        f.write(rec.tobytes())


def preview(parts, path: Path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection

    fig = plt.figure(figsize=(14, 7), dpi=110)
    for k, (title, items, elev, azim) in enumerate(parts):
        ax = fig.add_subplot(1, len(parts), k + 1, projection="3d")
        allv = []
        for m, color in items:
            mesh = m.to_mesh()
            v = np.asarray(mesh.vert_properties)[:, :3]
            t = np.asarray(mesh.tri_verts)
            tri = v[t]
            n = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
            n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)
            light = np.array([0.4, -0.6, 0.7]); light /= np.linalg.norm(light)

            shade = 0.45 + 0.55 * np.clip(n @ light, 0, 1)
            base = np.array(matplotlib.colors.to_rgb(color))
            pc = Poly3DCollection(tri, facecolors=np.clip(base[None] * shade[:, None], 0, 1), linewidths=0)
            ax.add_collection3d(pc)
            allv.append(v)
        V = np.vstack(allv)
        c = (V.max(0) + V.min(0)) / 2
        r = (V.max(0) - V.min(0)).max() / 2
        ax.set_xlim(c[0] - r, c[0] + r); ax.set_ylim(c[1] - r, c[1] + r); ax.set_zlim(c[2] - r, c[2] + r)
        ax.set_box_aspect((1, 1, 1))
        ax.view_init(elev=elev, azim=azim)
        ax.set_axis_off()
        ax.set_title(title)
    fig.tight_layout()
    fig.savefig(path)


def pi_dummy(p, d, z) -> Manifold:
    """Rough Pi Zero model for previews: PCB + receptacles + plug."""
    x0, y0 = d["pcb_x0"], d["pcb_y0"]
    m = rbox(x0, y0, z, x0 + p["pcb_w"], y0 + p["pcb_d"], z + p["pcb_t"], 3)
    top = z + p["pcb_t"]
    for px, w in ((p["port_hdmi_x"], 11.2), (p["port_usb_x"], 8), (p["port_pwr_x"], 8)):
        m += box(x0 + px - w / 2, y0 - 0.8, top, x0 + px + w / 2, y0 + 5, top + 2.8)
    m += box(x0 + 25, y0 + 10, top, x0 + 39, y0 + 24, top + 1.2 + p["heatsink_h"])  # SoC + heatsink
    m += box(x0 - 2.5, y0 + p["sd_center_y"] - 5.5, top, x0 + 12, y0 + p["sd_center_y"] + 5.5, top + 1.4)  # micro-SD
    return m


def plug(p, d, z):
    """Micro-USB plug + cable going to the hub, for previews."""
    x = d["pcb_x0"] + p["port_pwr_x"]
    zc = z + p["pcb_t"] + p["plug_zc"]
    m = box(x - 5.2, -16, zc - 3.6, x + 5.2, d["pcb_y0"] - 0.8, zc + 3.6)
    m += Manifold.cylinder(30, 1.8).rotate([90, 0, 0]).translate([x, -16, zc])
    return m


WHITE, BLACK = "#eeeeee", "#222222"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pis", type=int, default=P["pis"])
    ap.add_argument("--usb", action="store_true", help="also open the USB/OTG data port")
    ap.add_argument("--hdmi", action="store_true", help="also open the mini-HDMI port")
    ap.add_argument("--header", action="store_true", help="boards have a soldered GPIO header")
    ap.add_argument("--heatsink", type=float, default=P["heatsink_h"])
    a = ap.parse_args()
    p = dict(P, pis=a.pis, open_usb=a.usb, open_hdmi=a.hdmi, gpio_header=a.header, heatsink_h=a.heatsink)
    d = dims(p)

    here = Path(__file__).resolve().parent
    out = here / "stl"
    out.mkdir(exist_ok=True)
    T, L = tray(p), lid(p)
    assert T.status().name == "NoError" and L.status().name == "NoError"
    flip = lambda m: m.mirror([0, 0, 1]).translate([0, 0, p["lid_t"]])   # lid prints top-down
    Tw, Tb = split_tray(p, T)
    Lw, Lb = split_lid(p, d, L)
    assert abs(Tw.volume() + Tb.volume() - T.volume()) < 1e-3 and Lb.volume() > 1
    write_stl(T, out / "tray.stl")              # single-colour versions
    write_stl(flip(L), out / "lid.stl")
    write_stl(Tw, out / "tray_white.stl")       # two-colour versions: load each pair as ONE object
    write_stl(Tb, out / "tray_black.stl")
    write_stl(flip(Lw), out / "lid_white.stl")
    write_stl(flip(Lb), out / "lid_black.stl")

    # assembled + exploded previews
    H = d["pitch"]
    asm, exp = [], []
    for i in range(p["pis"]):
        asm += [(Tw.translate([0, 0, i * H]), WHITE), (Tb.translate([0, 0, i * H]), BLACK), (pi_dummy(p, d, i * H + d["pcb_bot"]), "#2e8b57"),
                (plug(p, d, i * H + d["pcb_bot"]), "#333333")]
        e = i * (H + 14)
        exp += [(Tw.translate([0, 0, e]), WHITE), (Tb.translate([0, 0, e]), BLACK), (pi_dummy(p, d, e + d["pcb_bot"] + 7), "#2e8b57")]
    for m, c in ((Lw, WHITE), (Lb, BLACK)):
        asm.append((m.translate([0, 0, p["pis"] * H + 0.01]), c))
        exp.append((m.translate([0, 0, p["pis"] * (H + 14) + 6]), c))
    preview([("assembled, port side", asm, 18, -60),
             ("exploded", exp, 22, 35),
             ("lid (from the front)", [(Lw, WHITE), (Lb, BLACK)], 70, 90)],
            here / "preview.png")

    total_h = d["stack_h"]
    print(f"tray pitch        {H:.1f} mm  (x{p['pis']})")
    print(f"footprint         {d['out_w'] + 2*(p['col_r']-0.1):.0f} x {d['out_d'] + 2*(p['col_r']-0.1):.0f} mm")
    print(f"tower height      {total_h:.1f} mm")
    print(f"clamp screws      4x M3 x {d['screw_l']} mm (head on the lid) + 4x M3 hex nut (pocket {d['nut_pocket']:.1f} mm deep under each column)")
    print(f"board screws      {4*p['pis']}x M2.5 heat-set inserts ({p['insert_len']:.0f} mm long, {p['insert_hole_d']} mm hole) + {4*p['pis']}x M2.5 x 5 mm machine screws")
    print(f"wrote {out}/{{tray,lid}}.stl (one colour) + {{tray,lid}}_{{white,black}}.stl (two colour), {here/'preview.png'}")


if __name__ == "__main__":
    main()
