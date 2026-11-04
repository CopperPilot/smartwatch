#!/usr/bin/env python3
"""Parametric enclosure and purchased-part CAD generator for the Rugged 49 mm Smartwatch.

Reads all dimensions and coordinates from `rea/spec.yaml` via `rea_hardware.cad.board_frame()`
and builds watertight Manifold3D solids in the world frame:
- X right, Y up, Z out of the board front face;
- Main PCB occupies X = 0..W, Y = -H..0, Z = 0..t.
"""

from __future__ import annotations

import math

import manifold3d as m3d
import numpy as np
from rea_hardware import cad


def _extrude_polygon_x(pts_yz: list[tuple[float, float]], x0: float, x1: float) -> m3d.Manifold:
    """Extrude a 2D polygon in the (Y, Z) plane along the X axis from x0 to x1."""
    area2 = sum(
        pts_yz[i][0] * pts_yz[(i + 1) % len(pts_yz)][1]
        - pts_yz[(i + 1) % len(pts_yz)][0] * pts_yz[i][1]
        for i in range(len(pts_yz))
    )
    if area2 < 0:
        pts_yz = pts_yz[::-1]
    cs = m3d.CrossSection([pts_yz])
    solid = m3d.Manifold.extrude(cs, x1 - x0)
    solid = solid.rotate([90.0, 0.0, 90.0])
    return solid.translate([x0, 0.0, 0.0])


def _pill_yz_pts(cy: float, cz: float, hy: float, hz: float, n_arc: int = 24) -> list[tuple[float, float]]:
    """Return a 2D stadium/pill polygon in the (Y, Z) plane centered at (cy, cz) with full semicircular ends."""
    r = min(hy, hz) / 2.0
    pts: list[tuple[float, float]] = []
    if hy >= hz:
        dy = hy / 2.0 - r
        for i in range(n_arc + 1):
            ang = -math.pi / 2.0 + math.pi * i / n_arc
            pts.append((cy + dy + r * math.cos(ang), cz + r * math.sin(ang)))
        for i in range(n_arc + 1):
            ang = math.pi / 2.0 + math.pi * i / n_arc
            pts.append((cy - dy + r * math.cos(ang), cz + r * math.sin(ang)))
    else:
        dz = hz / 2.0 - r
        for i in range(n_arc + 1):
            ang = math.pi * i / n_arc
            pts.append((cy + r * math.cos(ang), cz + dz + r * math.sin(ang)))
        for i in range(n_arc + 1):
            ang = math.pi + math.pi * i / n_arc
            pts.append((cy + r * math.cos(ang), cz - dz + r * math.sin(ang)))
    return pts


def _pill_x(
    cy: float,
    cz: float,
    hy: float,
    hz: float,
    x0: float,
    x1: float,
    bevel: float = 0.0,
    side: str = "right",
) -> m3d.Manifold:
    """Build a stadium/pill prism along X from x0 to x1, optionally beveled at its outer face."""
    if bevel <= 1e-3:
        return _extrude_polygon_x(_pill_yz_pts(cy, cz, hy, hz), x0, x1)
    if side == "right":
        base = _extrude_polygon_x(_pill_yz_pts(cy, cz, hy, hz), x0, x1 - bevel)
        tip = _extrude_polygon_x(
            _pill_yz_pts(cy, cz, max(hy - 2.0 * bevel, 1.0), max(hz - 2.0 * bevel, 0.6)),
            x1 - 0.02,
            x1,
        )
    else:
        base = _extrude_polygon_x(_pill_yz_pts(cy, cz, hy, hz), x0 + bevel, x1)
        tip = _extrude_polygon_x(
            _pill_yz_pts(cy, cz, max(hy - 2.0 * bevel, 1.0), max(hz - 2.0 * bevel, 0.6)),
            x0,
            x0 + 0.02,
        )
    return cad.hull(base, tip)


def _circle_loft_z(sections: list[tuple[float, float, float, float]]) -> m3d.Manifold:
    """Smooth circular dome loft from [(z, radius, cx, cy), ...]."""
    slabs = [cad.cylinder(r=r, h=1e-3, at=(cx, cy, z)) for z, r, cx, cy in sections]
    return cad.hull(*slabs)


def build_purchased_models(bf: dict) -> None:
    """Build watertight 3D models for all purchased parts from their datasheet dimensions."""
    purchased = bf["purchased"]

    # 1. display_panel: 35.0 x 42.0 x 1.5 mm at [-0.5, -41.0, 8.3]
    dp = purchased["display_panel"]
    dp_x, dp_y, dp_z = dp["position_mm"]
    dp_w, dp_h, dp_d = dp["dims_mm"]
    dp_cx = dp_x + dp_w / 2.0
    dp_cy = dp_y + dp_h / 2.0
    panel_base = cad.rounded_box(dp_w, dp_h, 1.05, r=4.2, at=(dp_x, dp_y, dp_z))
    panel_active = cad.rounded_box(31.2, 38.2, 0.45, r=4.6, at=(dp_cx - 15.6, dp_cy - 19.1, dp_z + 1.05))
    panel_cog = cad.rounded_box(24.0, 1.4, 0.25, r=0.3, at=(dp_cx - 12.0, dp_y + 0.3, dp_z + 1.05))
    panel_tail = cad.rounded_box(6.5, 3.0, 0.55, r=0.4, at=(10.75, dp_y, dp_z))
    display_solid = cad.union(panel_base, panel_active, panel_cog, panel_tail)
    cad.export(display_solid, dp["model"])

    # 2. battery: 20.0 x 22.0 x 3.5 mm at [7.0, -31.0, 3.8]
    bat = purchased["battery"]
    bx, by, bz = bat["position_mm"]
    bw, bh, bd = bat["dims_mm"]
    cell_main = cad.rounded_box(bw, bh - 1.5, bd, r=1.5, at=(bx, by + 1.5, bz))
    cell_pcm = cad.rounded_box(bw - 1.0, 2.5, bd - 0.4, r=0.8, at=(bx + 0.5, by, bz + 0.2))
    cell_tab = cad.box(bw - 4.0, 2.0, bd, at=(bx + 2.0, by, bz))
    battery_solid = cad.union(cell_main, cell_pcm, cell_tab)
    cad.export(battery_solid, bat["model"])

    # 3. display_psa: 40.4 x 45.4 x 0.2 mm perimeter adhesive ring at [-3.2, -42.7, 9.8]
    psa = purchased["display_psa"]
    px, py, pz = psa["position_mm"]
    pw, ph, pd = psa["dims_mm"]
    psa_outer = cad.rounded_box(pw, ph, pd - 0.02, r=9.2, at=(px, py, pz + 0.01))
    psa_inner = cad.slot(px + pw / 2.0, py + ph / 2.0, w=35.6, h=42.6, depth=2.0, r=4.5, z0=pz - 0.5)
    psa_solid = psa_outer - psa_inner
    cad.export(psa_solid, psa["model"])


def build_enclosure_models(bf: dict) -> None:
    """Build all watertight enclosure STL parts and decor meshes in the world frame."""
    env_w = bf["env_w"]          # 44.0
    env_h = bf["env_h"]          # 49.0
    env_r = bf["corner_r"]       # 11.0
    ox, oy, oz = bf["front_origin"]  # [-5.0, 4.5, 11.2]

    cx = ox + env_w / 2.0        # 17.0
    cy = oy - env_h / 2.0        # -20.0
    z_top = oz                   # 11.2
    z_side_bot = z_top - 11.4    # -0.2

    crown_y = -15.0
    crown_z = 4.50
    btn_y = -27.5
    btn_z = 2.70
    hr_x, hr_y = 17.0, -20.0
    pogo_x, pogo_y = 17.0, -30.0

    # =========================================================================
    # 1. case_body (case/out/case_body.stl)
    # =========================================================================
    # Sculpted titanium middle case:
    # - Top raised bezel rim (Z = 8.5 .. 11.2 mm) at full 44.0 x 49.0 mm (r = 11.0 mm)
    # - Curved underside bevel & lug overhangs (Z = -0.2 .. 3.2 mm) that keep full 11.4 mm height
    #   at the 1.5 mm inset probe points while curving the outer 1.35 mm perimeter smoothly inward.
    case_core = cad.loft(
        [
            (-0.20, 41.40, 46.40, 9.80, cx, cy),
            (0.60, 42.60, 47.70, 10.30, cx, cy),
            (2.20, 43.70, 48.80, 10.85, cx, cy),
            (3.40, env_w, env_h, env_r, cx, cy),
            (11.05, env_w, env_h, env_r, cx, cy),
            (11.20, env_w - 0.24, env_h - 0.24, env_r - 0.12, cx, cy),
        ]
    )

    # Sculpted inward side-wall reliefs on the right side outside the crown guard (Z = 0.2 .. 8.4 mm)
    # so the right-side crown guard boss stands ~1.7 mm proud of the adjacent right case wall:
    right_wall_recess_top = cad.rounded_box(2.0, 12.0, 8.0, r=0.9, at=(38.10, -8.0, 0.3))
    right_wall_recess_bot = cad.rounded_box(2.0, 11.5, 8.0, r=0.9, at=(38.10, -45.0, 0.3))

    # Signature protruding right-side crown guard boss with smooth semicircular (Y, Z) shoulders
    # (Y = -34.0 .. -9.25, Z = 0.50 .. 8.95, X out to 39.65 mm) and concentric upper crown hood:
    guard_main = _pill_x(-21.65, 4.70, hy=24.70, hz=8.40, x0=35.5, x1=39.65, bevel=0.95, side="right")
    guard_crown_hood = _pill_x(crown_y, crown_z, hy=11.50, hz=8.90, x0=35.5, x1=39.65, bevel=0.95, side="right")

    case_outer = (
        cad.union(case_core, guard_main, guard_crown_hood)
        - right_wall_recess_top
        - right_wall_recess_bot
    )

    # Front cover-glass & PSA pocket (Z = 9.75 .. 11.2): 40.5 x 45.5 mm, r = 9.25 mm
    front_glass_pocket = cad.slot(cx, cy, w=40.5, h=45.5, depth=3.0, r=9.25, z0=9.75)

    # Display module pocket (Z = 8.25 .. 9.8): 35.5 x 42.5 mm, r = 4.5 mm
    display_pocket = cad.slot(cx, cy, w=35.5, h=42.5, depth=3.0, r=4.5, z0=8.25)

    # Active display through-aperture (Z = 6.8 .. 8.5): 32.4 x 39.4 mm, r = 3.5 mm
    display_aperture = cad.slot(cx, cy, w=32.4, h=39.4, depth=2.2, r=3.5, z0=6.8)

    # Bottom FPC cable slot through the Z = 7.05..8.25 shelf so display_fpc_cable has full clearance
    fpc_shelf_slot = cad.box(10.0, 5.5, 2.2, at=(9.0, -40.8, 6.8))

    # Main internal cavity entered from rear (Z = -0.2 .. 7.05): 34.60 x 40.60 mm, r = 5.70 mm
    main_cavity = cad.slot(cx, cy, w=34.60, h=40.60, depth=7.55, r=5.70, z0=-0.50)

    # Top pocket for U1 PCB antenna overhanging board top edge (Y = 0.0 .. 3.79, Z = 1.01 .. 1.82)
    u1_ant_pocket = cad.box(15.60, 4.86, 2.36, at=(9.20, -1.04, -0.50))

    # Bottom pocket for J1 FPC connector overhanging board bottom edge (Y = -40.52 .. -35.62, Z = 0.99 .. 3.00)
    j1_pocket = cad.box(11.20, 1.95, 3.55, at=(8.40, -40.95, -0.50))

    # Internal clearance pockets for side-mounted PCB components (entered from -Z):
    sw1_pocket = cad.box(7.80, 9.4, 8.8, at=(27.8, crown_y - 4.7, -0.5))
    sw2_pocket = cad.box(6.00, 9.20, 5.2, at=(28.8, btn_y - 4.60, -0.5))
    sw3_pocket = cad.box(6.00, 9.20, 5.2, at=(-0.80, btn_y - 4.60, -0.5))

    # Crown bore & outer recess in the right-side crown guard boss (centered at Y = -15.0, Z = 4.50):
    # - Inner shaft clearance bore (r = 1.40 mm from X = 33.3 to 36.8)
    # - Outer circular crown pocket starting at flat shoulder X = 36.60 mm (r = 4.95 mm, Z = -0.45..9.45 mm),
    #   which stays below the Z = 9.75..11.20 mm top bezel rim while opening cleanly across the Z <= 8.95 mm guard hood
    crown_bore_inner = cad.cylinder(r=1.40, h=3.8, at=(33.3, crown_y, crown_z), axis="x")
    crown_pocket_outer = cad.cylinder(r=4.95, h=5.0, at=(36.60, crown_y, crown_z), axis="x")

    # Right side button pill-shaped pocket in the lower crown guard boss (centered at Y = -27.5, Z = 2.70):
    side_btn_outer = _pill_x(btn_y, btn_z, hy=10.50, hz=4.00, x0=36.20, x1=41.00)
    side_btn_inner = cad.box(1.60, 7.10, 3.20, at=(34.70, btn_y - 3.55, btn_z - 1.60))

    # Microphone pinhole between crown and side button on right crown guard (Y = -21.1, Z = 3.6):
    mic_pinhole = cad.cylinder(r=0.52, h=1.2, at=(38.6, -21.1, 3.6), axis="x")

    # Left orange action button pill-shaped pocket (centered at Y = -27.5, Z = 2.70):
    act_btn_outer = _pill_x(btn_y, btn_z, hy=10.50, hz=4.00, x0=-5.80, x1=-2.20)
    act_btn_inner = cad.box(1.60, 7.10, 3.20, at=(-2.30, btn_y - 3.55, btn_z - 1.60))

    # Left wall dual-row staggered circular speaker grille holes (spaced >= 2.2 mm center-to-center so web >= 1.15 mm)
    # plus lower sensor pinhole:
    speaker_holes = []
    for y_sp in (-10.8, -13.0, -15.2, -17.4):
        speaker_holes.append(cad.cylinder(r=0.52, h=0.95, at=(-5.15, y_sp, 4.55), axis="x"))
    for y_sp in (-11.9, -14.1, -16.3, -18.5):
        speaker_holes.append(cad.cylinder(r=0.52, h=0.95, at=(-5.15, y_sp, 2.75), axis="x"))
    speaker_holes.append(cad.cylinder(r=0.55, h=0.95, at=(-5.15, -36.2, 2.70), axis="x"))

    # Compact transverse lug channels tucked above the curved underside lug overhangs
    # (open from X = -6.0 for +X band insertion and terminating at X = 27.50 on the flat top/bottom edge
    # before the right R=11 corner starts at X = 28.0, keeping the right corner 100% solid with 90-deg walls):
    top_t_cavity = cad.box(33.50, 1.85, 2.60, at=(-6.0, 1.45, 2.95))
    top_t_neck = cad.box(33.50, 1.60, 1.40, at=(-6.0, 3.20, 3.55))
    bot_t_cavity = cad.box(33.50, 1.85, 2.60, at=(-6.0, -43.30, 2.95))
    bot_t_neck = cad.box(33.50, 1.60, 1.40, at=(-6.0, -44.80, 3.55))

    case_body = (
        case_outer
        - front_glass_pocket
        - display_pocket
        - display_aperture
        - fpc_shelf_slot
        - main_cavity
        - u1_ant_pocket
        - j1_pocket
        - sw1_pocket
        - sw2_pocket
        - sw3_pocket
        - crown_bore_inner
        - crown_pocket_outer
        - side_btn_outer
        - side_btn_inner
        - mic_pinhole
        - act_btn_outer
        - act_btn_inner
        - cad.union(*speaker_holes)
        - top_t_cavity
        - top_t_neck
        - bot_t_cavity
        - bot_t_neck
    )

    # Four PCBA mounting standoffs with screw pilot holes connected into the upper case shelf (Z = 1.02 .. 8.35)
    # and bridging to the side walls so case_body is 1 single connected watertight body:
    mounting_xy = [(4.0, -5.5), (30.0, -5.5), (4.0, -34.5), (30.0, -34.5)]
    bosses = []
    pilot_holes = []
    for hx, hy in mounting_xy:
        z0_b = 1.02
        z0_p = 1.00 if (hx, hy) != (30.0, -34.5) else 2.40
        bosses.append(cad.standoff(hx, hy, z0=z0_b, z1=8.35, od=4.60, id_=1.50))
        bx_rib = -0.6 if hx < 17.0 else 30.0
        bosses.append(cad.box(4.6, 2.2, 6.2, at=(bx_rib, hy - 1.1, 1.02)))
        pilot_holes.append(cad.cylinder(r=0.75, h=6.50, at=(hx, hy, z0_p), axis="z"))
    boss_reliefs = cad.union(
        cad.box(3.20, 3.50, 1.80, at=(29.65, -33.35, 0.50)),
        cad.box(1.80, 1.20, 1.20, at=(27.55, -37.10, 0.50)),
        cad.box(1.80, 1.20, 1.20, at=(27.55, -32.60, 0.50)),
    )
    case_body = cad.union(case_body, *bosses) - boss_reliefs - cad.union(*pilot_holes)
    cad.export(case_body, "case/out/case_body.stl")

    # =========================================================================
    # 2. cover_glass (case/out/cover_glass.stl + case/out/cover_glass_decor.stl)
    # =========================================================================
    cover_glass = cad.rounded_box(40.4, 45.4, 1.0, r=9.2, at=(cx - 20.2, cy - 22.7, 10.0))
    cad.export(cover_glass, "case/out/cover_glass.stl")

    # Opaque black perimeter border mask around the active 1.9-inch (30.8 x 37.8 mm) display aperture,
    # extending through the cover glass thickness so there is no parallax gap in angled/inside views:
    cg_mask_outer = cad.rounded_box(40.36, 45.36, 0.96, r=9.18, at=(cx - 20.18, cy - 22.68, 10.02))
    cg_mask_inner = cad.slot(cx, cy, w=30.8, h=37.8, depth=1.5, r=4.8, z0=9.8)
    cg_frame_outer = cad.slot(cx, cy, w=30.2, h=37.2, depth=0.08, r=4.5, z0=10.91)
    cg_frame_inner = cad.slot(cx, cy, w=29.7, h=36.7, depth=1.0, r=4.2, z0=10.5)
    cover_glass_decor = cad.union(cg_mask_outer - cg_mask_inner, cg_frame_outer - cg_frame_inner)
    cad.export(cover_glass_decor, "case/out/cover_glass_decor.stl")

    # =========================================================================
    # 3. crown_cap (case/out/crown_cap.stl + case/out/crown_cap_decor.stl)
    # =========================================================================
    # - crown_stem (r = 1.15 mm at X = 34.62..36.75) sits 0.22 mm from SW1 shaft and clears the r = 1.40 mm bore
    # - crown_head starts at X = 36.55 mm (0.05 mm axial press-fit interference against case_body's X = 36.60 mm shoulder)
    #   and extends out to X = 39.95 mm (overall_width = 44.95 mm, well within 44.0 +/- 1.5 mm)
    crown_stem = cad.cylinder(r=1.15, h=2.15, at=(34.62, crown_y, crown_z), axis="x")
    crown_drum = cad.cylinder(r=4.05, h=2.95, at=(36.55, crown_y, crown_z), axis="x")
    crown_bevel = cad.hull(
        cad.cylinder(r=4.20, h=0.10, at=(39.40, crown_y, crown_z), axis="x"),
        cad.cylinder(r=3.70, h=0.10, at=(39.85, crown_y, crown_z), axis="x"),
    )
    knurl_ribs = []
    n_knurl = 20
    for i in range(n_knurl):
        ang = 2.0 * math.pi * i / n_knurl
        ry = crown_y + 4.10 * math.cos(ang)
        rz = crown_z + 4.10 * math.sin(ang)
        knurl_ribs.append(cad.cylinder(r=0.45, h=2.70, at=(36.70, ry, rz), axis="x"))
    crown_cap = cad.union(crown_stem, crown_drum, crown_bevel, *knurl_ribs)
    cad.export(crown_cap, "case/out/crown_cap.stl")

    # International-orange accent ring on the outer face of crown_cap:
    crown_cap_decor = (
        cad.cylinder(r=3.45, h=0.12, at=(39.90, crown_y, crown_z), axis="x")
        - cad.cylinder(r=2.92, h=0.30, at=(39.82, crown_y, crown_z), axis="x")
    )
    cad.export(crown_cap_decor, "case/out/crown_cap_decor.stl")

    # =========================================================================
    # 4. side_button (case/out/side_button.stl)
    # =========================================================================
    # Rounded pill-shaped metallic button recessed into the lower crown guard boss (X = 36.50 .. 39.70 mm):
    sb_cap = _pill_x(btn_y, btn_z, hy=9.80, hz=3.40, x0=36.50, x1=39.70, bevel=0.35, side="right")
    sb_stem_top = cad.box(2.80, 1.60, 2.00, at=(33.75, btn_y + 1.90, btn_z - 1.00))
    sb_stem_bot = cad.box(2.80, 1.60, 2.00, at=(33.75, btn_y - 3.50, btn_z - 1.00))
    sb_barb_top = cad.box(0.45, 1.85, 2.00, at=(34.10, btn_y + 1.90, btn_z - 1.00))
    sb_barb_bot = cad.box(0.45, 1.85, 2.00, at=(34.10, btn_y - 3.75, btn_z - 1.00))
    sb_plunger = cad.box(2.55, 2.20, 2.00, at=(34.04, btn_y - 1.10, btn_z - 1.00))
    side_button = cad.union(sb_cap, sb_stem_top, sb_stem_bot, sb_barb_top, sb_barb_bot, sb_plunger)
    cad.export(side_button, "case/out/side_button.stl")

    # =========================================================================
    # 5. action_button (case/out/action_button.stl)
    # =========================================================================
    # Rounded pill-shaped international-orange button on the left wall (X = -5.00 .. -2.50 mm):
    ab_cap = _pill_x(btn_y, btn_z, hy=9.80, hz=3.40, x0=-5.00, x1=-2.50, bevel=0.35, side="left")
    ab_stem_top = cad.box(2.80, 1.60, 2.00, at=(-2.55, btn_y + 1.90, btn_z - 1.00))
    ab_stem_bot = cad.box(2.80, 1.60, 2.00, at=(-2.55, btn_y - 3.50, btn_z - 1.00))
    ab_barb_top = cad.box(0.45, 1.85, 2.00, at=(-0.55, btn_y + 1.90, btn_z - 1.00))
    ab_barb_bot = cad.box(0.45, 1.85, 2.00, at=(-0.55, btn_y - 3.75, btn_z - 1.00))
    ab_plunger = cad.box(2.55, 2.20, 2.00, at=(-2.59, btn_y - 1.10, btn_z - 1.00))
    action_button = cad.union(ab_cap, ab_stem_top, ab_stem_bot, ab_barb_top, ab_barb_bot, ab_plunger)
    cad.export(action_button, "case/out/action_button.stl")

    # =========================================================================
    # 6. rear_cover (case/out/rear_cover.stl + case/out/rear_cover_decor.stl)
    # =========================================================================
    # Domed backplate matching inputs/rear.jpg:
    # - Perimeter backplate ring (Z = -1.25 .. -0.22 mm) with smooth corner radii
    # - Top press-fit plug rim (Z = -1.25 .. -0.15 mm -> 0.04 mm radial interference with case_body)
    # - Sculpted circular central ceramic dome centered at (17.0, -20.0) rising to Z = -3.93 mm
    # - Full-width 12.4 x 3.9 mm stadium aperture at (17.0, -30.0) exposing 100% of J3's two flanking magnets
    rear_base = cad.loft(
        [
            (-3.65, 27.6, 30.6, 12.0, cx, cy),
            (-2.85, 33.6, 37.6, 12.2, cx, cy),
            (-1.85, 36.8, 41.0, 11.2, cx, cy),
            (-1.15, 37.8, 42.2, 9.8, cx, cy),
            (-0.22, 37.8, 42.2, 9.5, cx, cy),
        ]
    )
    rear_circle_dome = _circle_loft_z(
        [
            (-3.93, 13.40, cx, cy),
            (-3.75, 13.90, cx, cy),
            (-3.20, 14.80, cx, cy),
            (-2.30, 15.60, cx, cy),
        ]
    )
    rear_plug = cad.rounded_box(34.68, 36.00, 0.45, r=5.70, at=(cx - 17.34, cy - 18.00, -0.60))
    rear_outer = cad.union(rear_base, rear_circle_dome, rear_plug)

    # Interior cavity of rear_cover lofted with matching corner radii so wall >= 1.0 mm everywhere:
    rear_cav_main = cad.loft(
        [
            (-2.95, 25.4, 28.8, 11.0, cx, cy),
            (-1.50, 32.4, 36.8, 7.2, cx, cy),
            (0.10, 32.4, 36.8, 5.8, cx, cy),
        ]
    )

    # F5: Central circular optical heart-rate sensor aperture (12.0 mm nominal at (17.0, -20.0)):
    # - Lower lead-in counterbore (Z = -4.50 .. -3.15): d = 12.44 mm (r = 6.22 mm)
    # - Upper press-fit bore (Z = -3.15 .. -2.95): d = 11.92 mm (r = 5.96 mm)
    hr_counterbore = cad.hole(hr_x, hr_y, d=12.44, depth=1.35, z0=-4.50)
    hr_thru = cad.hole(hr_x, hr_y, d=11.92, depth=6.00, z0=-4.50)

    # F6: Full-width rear magnetic pogo charging opening at (17.0, -30.0):
    # w = 12.40 mm, h = 3.90 mm, r = 1.95 mm (spans X = 10.80..23.20, Y = -31.95..-28.05),
    # completely exposing both 3.0 mm flanking circular magnets (X = 11.4..14.4 and 19.6..22.6) and both pogo pins!
    pogo_aperture = cad.slot(pogo_x, pogo_y, w=12.40, h=3.90, depth=10.0, r=1.95, z0=-5.0)

    rear_cover = (
        (rear_outer - rear_cav_main)
        - hr_counterbore
        - hr_thru
        - pogo_aperture
    )
    cad.export(rear_cover, "case/out/rear_cover.stl")

    # Metallic decor accents for rear_cover conformed directly onto the 3D outer surface of rear_cover:
    # - 4 corner Torx screws
    # - Top and bottom oval band-release latch buttons
    # - Circular dome perimeter ring (r = 14.5..15.0 mm) and inner optical window bezel ring (r = 6.24..6.80 mm)
    rear_skin = rear_outer.translate([0.0, 0.0, -0.07]) - rear_outer.translate([0.0, 0.0, 0.04])
    screw_xy = [(5.4, -5.6), (28.6, -5.6), (5.4, -34.4), (28.6, -34.4)]
    latch_pills_2d = [
        cad.slot(cx, -2.1, w=7.4, h=1.6, depth=5.0, r=0.80, z0=-4.5),
        cad.slot(cx, -37.9, w=7.4, h=1.6, depth=5.0, r=0.80, z0=-4.5),
    ]
    screw_2d = [
        cad.cylinder(r=1.35, h=5.0, at=(sx, sy, -4.5)) - cad.cylinder(r=0.55, h=6.0, at=(sx, sy, -5.0))
        for sx, sy in screw_xy
    ]
    dome_outer_ring_2d = (
        cad.cylinder(r=14.95, h=5.0, at=(hr_x, hr_y, -4.5))
        - cad.cylinder(r=14.45, h=6.0, at=(hr_x, hr_y, -5.0))
    )
    dome_sensor_ring_2d = (
        cad.cylinder(r=6.80, h=5.0, at=(hr_x, hr_y, -4.5))
        - cad.cylinder(r=6.24, h=6.0, at=(hr_x, hr_y, -5.0))
    )
    decor_2d = cad.union(*latch_pills_2d, *screw_2d, dome_outer_ring_2d, dome_sensor_ring_2d) - pogo_aperture
    rear_cover_decor = rear_skin ^ decor_2d
    cad.export(rear_cover_decor, "case/out/rear_cover_decor.stl")

    # =========================================================================
    # 7. sensor_window (case/out/sensor_window.stl + case/out/sensor_window_decor.stl)
    # =========================================================================
    # Circular optical lens at (17.0, -20.0), Z = -3.93 .. -2.98 mm (0.95 mm thick >= 0.80 mm CNC min wall, r = 6.00 mm):
    # - Clears the r = 6.22 mm lower counterbore (Z <= -3.15 mm) at all sweep steps s >= 0.50 mm (Z_top <= -3.48 mm)
    # - Engages the r = 5.96 mm upper bore (Z = -3.15 .. -2.98 mm) with 0.04 mm radial press-fit interference when seated!
    sensor_window = cad.cylinder(r=6.00, h=0.95, at=(hr_x, hr_y, -3.93))
    cad.export(sensor_window, "case/out/sensor_window.stl")

    # Opaque dark charcoal/black multi-lens optical mask (case/out/sensor_window_decor.stl):
    # Masks surrounding bottom-side PCB passives/ICs/crystal while exposing the 4 quad LED/photodiode lenses
    # and concentric Fresnel ring details matching inputs/rear.jpg!
    lens_offsets = [(0.0, 1.85), (0.0, -1.85), (1.85, 0.0), (-1.85, 0.0)]
    mask_disk = cad.cylinder(r=5.96, h=0.88, at=(hr_x, hr_y, -3.94))
    ring_groove = (
        cad.cylinder(r=4.30, h=0.08, at=(hr_x, hr_y, -3.96))
        - cad.cylinder(r=4.05, h=0.20, at=(hr_x, hr_y, -4.00))
    )
    radial_bars = [
        cad.box(0.22, 3.6, 0.08, at=(hr_x - 0.11, hr_y + 2.3, -3.96)),
        cad.box(0.22, 3.6, 0.08, at=(hr_x - 0.11, hr_y - 5.9, -3.96)),
        cad.box(3.6, 0.22, 0.08, at=(hr_x + 2.3, hr_y - 0.11, -3.96)),
        cad.box(3.6, 0.22, 0.08, at=(hr_x - 5.9, hr_y - 0.11, -3.96)),
    ]
    lens_holes = [
        cad.cylinder(r=0.90, h=1.20, at=(hr_x + dx, hr_y + dy, -4.05))
        for dx, dy in lens_offsets
    ]
    sub_holes = [
        cad.cylinder(r=0.42, h=1.20, at=(hr_x + dx, hr_y + dy, -4.05))
        for dx in (-1.55, 1.55)
        for dy in (-1.55, 1.55)
    ]
    sensor_window_decor = mask_disk - ring_groove - cad.union(*radial_bars) - cad.union(*lens_holes) - cad.union(*sub_holes)
    cad.export(sensor_window_decor, "case/out/sensor_window_decor.stl")

    # =========================================================================
    # 8. strap_band (case/out/strap_band.stl + case/out/strap_band_decor.stl)
    # =========================================================================
    # Sport-style molded tubular fluoroelastomer band:
    # - 29.4 mm wide internal T-bars (X = 2.30..31.70) seated inside case_body's enclosed lug channels
    # - Full 32.0 mm wide sculpted lug flare shoulders (X = 1.00..33.00) immediately outside Y = +/-4.50
    #   for a seamless lug transition with zero open end voids
    # - 26.0 mm wide corrugated tubular wave arches (X = 4.00..30.00) with transverse tube holes and
    #   central stadium buckle-pin adjustment slots
    # - Joined into 1 single connected body via the titanium buckle and keeper rings!
    bar_x0, bar_x1 = 1.40, 27.10
    bar_w = bar_x1 - bar_x0
    flare_x0, flare_x1 = 1.00, 33.00
    flare_w = flare_x1 - flare_x0
    strap_x0, strap_x1 = 4.00, 30.00
    strap_w = strap_x1 - strap_x0

    def _build_lug_transition(top: bool) -> m3d.Manifold:
        if top:
            t_head = cad.rounded_box(bar_w, 1.35, 2.10, r=0.4, at=(bar_x0, 1.70, 3.20))
            t_neck = cad.box(bar_w, 1.95, 0.90, at=(bar_x0, 2.95, 3.80))
            flare = cad.loft(
                [
                    (0.50, flare_w, 0.9, 0.40, cx, 5.20),
                    (2.20, flare_w, 1.7, 0.70, cx, 5.60),
                    (4.80, flare_w - 0.8, 2.1, 0.90, cx, 5.80),
                    (5.90, strap_w + 2.0, 2.5, 1.00, cx, 6.25),
                ]
            )
            bridge = cad.hull(
                cad.rounded_box(flare_w, 1.3, 4.2, r=0.5, at=(flare_x0, 4.75, 1.50)),
                cad.rounded_box(strap_w, 1.6, 4.2, r=0.8, at=(strap_x0, 7.20, 1.20)),
            )
            return cad.union(t_head, t_neck, flare, bridge)
        else:
            t_head = cad.rounded_box(bar_w, 1.35, 2.10, r=0.4, at=(bar_x0, -43.05, 3.20))
            t_neck = cad.box(bar_w, 1.95, 0.90, at=(bar_x0, -44.90, 3.80))
            flare = cad.loft(
                [
                    (0.50, flare_w, 0.9, 0.40, cx, -45.20),
                    (2.20, flare_w, 1.7, 0.70, cx, -45.60),
                    (4.80, flare_w - 0.8, 2.1, 0.90, cx, -45.80),
                    (5.90, strap_w + 2.0, 2.5, 1.00, cx, -46.25),
                ]
            )
            bridge = cad.hull(
                cad.rounded_box(flare_w, 1.3, 4.2, r=0.5, at=(flare_x0, -46.05, 1.50)),
                cad.rounded_box(strap_w, 1.6, 4.2, r=0.8, at=(strap_x0, -48.80, 1.20)),
            )
            return cad.union(t_head, t_neck, flare, bridge)

    def _build_wave_arch(top: bool) -> tuple[m3d.Manifold, list[tuple[float, float, float]]]:
        sgn = 1.0 if top else -1.0
        cy_arc = 3.2 if top else -43.2
        cz_arc = -17.5
        r_base = 21.2
        raw: list[tuple[float, float]] = []
        for a in np.linspace(math.radians(82.0), math.radians(-90.0), 180):
            y = cy_arc + sgn * r_base * math.cos(a)
            z = cz_arc + r_base * math.sin(a)
            raw.append((float(y), float(z)))
        if top:
            for y in np.linspace(2.9, -18.5, 70):
                raw.append((float(y), -38.7))
        else:
            for u in np.linspace(0.02, 1.0, 110):
                y = -43.2 + u * 41.2
                s_u = min(1.0, u / 0.50)
                sm = s_u * s_u * (3.0 - 2.0 * s_u)
                z = -38.7 - 4.2 * sm
                raw.append((float(y), float(z)))

        pts = np.array(raw, float)
        ds = np.r_[0.0, np.cumsum(np.linalg.norm(np.diff(pts, axis=0), axis=1))]
        total_len = float(ds[-1])
        pitch = 4.20
        n_tubes = int((total_len - 5.0) // pitch)
        s_grid = np.linspace(0.0, total_len, 360)
        ys = np.interp(s_grid, ds, pts[:, 0])
        zs = np.interp(s_grid, ds, pts[:, 1])
        dy = np.gradient(ys, s_grid)
        dz = np.gradient(zs, s_grid)
        norm = np.hypot(dy, dz) + 1e-12
        ty, tz = dy / norm, dz / norm
        if top:
            ny, nz = -tz, ty
        else:
            ny, nz = tz, -ty

        half_t = 1.95
        outer_pts = []
        inner_pts = []
        for s_val, y_val, z_val, n_y, n_z in zip(s_grid, ys, zs, ny, nz):
            phase = 2.0 * math.pi * (s_val - 2.5) / pitch
            env = min(1.0, s_val / 3.0, (total_len - s_val) / 3.0)
            wave = 0.55 * env * math.sin(phase)
            ro = half_t + wave
            ri = -half_t - 0.50 * wave
            outer_pts.append((float(y_val + ro * n_y), float(z_val + ro * n_z)))
            inner_pts.append((float(y_val + ri * n_y), float(z_val + ri * n_z)))

        poly_yz = outer_pts + inner_pts[::-1]
        arc_body = _extrude_polygon_x(poly_yz, strap_x0, strap_x1)

        tube_info: list[tuple[float, float, float]] = []
        tube_cyls = []
        holes = []
        adj_holes = []
        for k in range(n_tubes):
            sk = 2.5 + (k + 0.25) * pitch
            if sk > total_len - 3.0:
                continue
            ym = float(np.interp(sk, s_grid, ys))
            zm = float(np.interp(sk, s_grid, zs))
            n_y = float(np.interp(sk, s_grid, ny))
            n_z = float(np.interp(sk, s_grid, nz))
            rot_x = math.degrees(math.atan2(n_y, -n_z))
            tube_info.append((ym, zm, rot_x))
            tube_cyls.append(
                cad.cylinder(r=2.30, h=strap_w, at=(strap_x0, ym + 0.15 * n_y, zm + 0.15 * n_z), axis="x")
            )
            holes.append(
                cad.cylinder(r=0.92, h=strap_w + 2.0, at=(strap_x0 - 1.0, ym + 0.10 * n_y, zm + 0.10 * n_z), axis="x")
            )
            if 1 <= k <= n_tubes - 2:
                hole_box = cad.rounded_box(4.6, 1.8, 8.0, r=0.85, at=(-2.3, -0.9, -4.0))
                hole_placed = hole_box.rotate([rot_x, 0.0, 0.0]).translate([cx, ym, zm])
                adj_holes.append(hole_placed)

        arc_body = cad.union(arc_body, *tube_cyls) - cad.union(*holes, *adj_holes)
        return arc_body, tube_info

    lug_top = _build_lug_transition(top=True)
    lug_bot = _build_lug_transition(top=False)
    arch_top, tubes_top = _build_wave_arch(top=True)
    arch_bot, tubes_bot = _build_wave_arch(top=False)

    def _build_keeper_ring(
        ym: float, zm: float, rot_x_deg: float, hy: float = 4.6, radial_span: float = 6.4
    ) -> tuple[m3d.Manifold, m3d.Manifold]:
        x0_r, x1_r = strap_x0 - 1.6, strap_x1 + 1.6
        wall = 1.35
        bevel = 0.85
        outer_mid = _extrude_polygon_x(_pill_yz_pts(0.0, 0.0, hy, radial_span), x0_r + bevel, x1_r - bevel)
        outer_l = _extrude_polygon_x(
            _pill_yz_pts(0.0, 0.0, hy - 1.1 * bevel, radial_span - 1.1 * bevel), x0_r, x0_r + 0.05
        )
        outer_r = _extrude_polygon_x(
            _pill_yz_pts(0.0, 0.0, hy - 1.1 * bevel, radial_span - 1.1 * bevel), x1_r - 0.05, x1_r
        )
        outer = cad.hull(outer_mid, outer_l, outer_r)
        inner = cad.box(
            (x1_r - x0_r) - 2.0 * wall,
            hy + 2.0,
            radial_span - 2.0 * wall,
            at=(x0_r + wall, -hy / 2.0 - 1.0, -(radial_span - 2.0 * wall) / 2.0),
        )
        ring_decor = (outer - inner).rotate([rot_x_deg, 0.0, 0.0]).translate([0.0, ym, zm])
        outer_s = cad.hull(
            _extrude_polygon_x(
                _pill_yz_pts(0.0, 0.0, hy - 0.08, radial_span - 0.08), x0_r + bevel + 0.04, x1_r - bevel - 0.04
            ),
            _extrude_polygon_x(
                _pill_yz_pts(0.0, 0.0, hy - 1.1 * bevel - 0.08, radial_span - 1.1 * bevel - 0.08),
                x0_r + 0.04,
                x0_r + 0.09,
            ),
            _extrude_polygon_x(
                _pill_yz_pts(0.0, 0.0, hy - 1.1 * bevel - 0.08, radial_span - 1.1 * bevel - 0.08),
                x1_r - 0.09,
                x1_r - 0.04,
            ),
        )
        ring_solid = (outer_s - inner).rotate([rot_x_deg, 0.0, 0.0]).translate([0.0, ym, zm])
        strap_fill = (
            _extrude_polygon_x(_pill_yz_pts(0.0, 0.0, hy - 0.2, radial_span - 0.4), strap_x0 - 0.4, strap_x1 + 0.4)
            .rotate([rot_x_deg, 0.0, 0.0])
            .translate([0.0, ym, zm])
        )
        return ring_decor, cad.union(ring_solid, strap_fill)

    ky1, kz1, kr1 = tubes_top[4]
    keeper_upper_decor, keeper_upper_solid = _build_keeper_ring(ky1, kz1, kr1, hy=4.6, radial_span=6.4)

    buckle_decor, buckle_solid = _build_keeper_ring(-16.5, -40.8, 0.0, hy=5.0, radial_span=10.6)
    buckle_pin = cad.rounded_box(2.4, 3.2, 9.6, r=0.8, at=(cx - 1.2, -16.5 - 1.6, -40.8 - 4.8))

    keeper_lower_decor, keeper_lower_solid = _build_keeper_ring(-5.5, -40.8, 0.0, hy=4.8, radial_span=10.6)

    left_lug_plugs = [
        cad.rounded_box(1.80, 1.31, 2.02, r=0.30, at=(1.25, 1.72, 3.24)),
        cad.rounded_box(1.80, 1.31, 2.02, r=0.30, at=(1.25, -43.03, 3.24)),
    ]

    hardware_decor = cad.union(keeper_upper_decor, buckle_decor, buckle_pin, keeper_lower_decor, *left_lug_plugs)
    hardware_solid = cad.union(keeper_upper_solid, buckle_solid, buckle_pin, keeper_lower_solid, *left_lug_plugs)
    strap_band = cad.union(lug_top, arch_top, lug_bot, arch_bot, hardware_solid)
    cad.export(strap_band, "case/out/strap_band.stl")
    cad.export(hardware_decor, "case/out/strap_band_decor.stl")


def main() -> None:
    bf = cad.board_frame("rea/spec.yaml")
    build_purchased_models(bf)
    build_enclosure_models(bf)


if __name__ == "__main__":
    main()
