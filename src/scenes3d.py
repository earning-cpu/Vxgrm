"""3D-world paper-cutout scenes for all 12 shots of 'काका मला वाचवा'."""
import math
from typing import Dict, Tuple
from src.world3d import World3D, Camera3D, Layer3D, load_rgba

_CACHE: Dict[str, object] = {}


def _get(name: str, max_dim: int = 1600):
    key = (name, max_dim)
    if key not in _CACHE:
        _CACHE[key] = load_rgba(f"assets/layers/{name}.png", max_dim=max_dim)
    return _CACHE[key]


def _make_plate_world(prefix: str, bg_z=1800, mid_z=1050, fg_z=420) -> World3D:
    w = World3D(1080, 1920)
    w.add(Layer3D(f"{prefix}_bg", _get(f"{prefix}_bg"), x=0, y=0, z=bg_z,
                  scale=1.95, shadow=False))
    w.add(Layer3D(f"{prefix}_mid", _get(f"{prefix}_mid"), x=0, y=0, z=mid_z,
                  scale=1.18, shadow=True, shadow_offset=(12, 16), shadow_alpha=0.45))
    w.add(Layer3D(f"{prefix}_fg", _get(f"{prefix}_fg"), x=0, y=0, z=fg_z,
                  scale=0.52, shadow=True, shadow_offset=(18, 24), shadow_alpha=0.55))
    return w


def build_scenes() -> Dict[str, Tuple[World3D, callable]]:
    """Return {shot_name: (World3D, camera_fn(t_local, dur) -> Camera3D)}."""
    scenes = {}

    # 1. Hook
    w_hook = _make_plate_world("hook")
    def cam_hook(tl, dur):
        p = min(1.0, tl / max(0.1, dur))
        sh = 10.0 * math.sin(tl * 42.0) * max(0.0, 1.0 - p * 0.6)
        return Camera3D(x=0, y=-20 * p, z=140 * p, focal=900, shake_x=sh, shake_y=sh * 0.6)
    scenes["hook"] = (w_hook, cam_hook)

    # 2. Gate (with drifting clouds + full moon)
    w_gate = _make_plate_world("gate")
    w_gate.add(Layer3D("moon", _get("prop_moon", 400), x=240, y=-520, z=1600,
                       scale=1.2, shadow=False, step_fps=12))
    w_gate.add(Layer3D("cloud1", _get("prop_cloud", 600), x=-300, y=-460, z=1400,
                       scale=1.4, opacity=0.85, step_fps=12,
                       animate=lambda l, tl, tg: setattr(l, "x", -350 + tl * 75)))
    def cam_gate(tl, dur):
        p = min(1.0, tl / max(0.1, dur))
        return Camera3D(x=-40 + 80 * p, y=20 - 40 * p, z=110 * p, focal=900)
    scenes["gate"] = (w_gate, cam_gate)

    # 3. Letter & 4. Alteration
    w_let = _make_plate_world("letter")
    def cam_let(tl, dur):
        p = min(1.0, tl / max(0.1, dur))
        return Camera3D(x=30 * math.sin(p * 1.5), y=-15 * p, z=120 * p, focal=900)
    scenes["letter"] = (w_let, cam_let)

    w_alt = _make_plate_world("letter")
    def cam_alt(tl, dur):
        p = min(1.0, tl / max(0.1, dur))
        sh = 6.0 * math.sin(tl * 35) if p > 0.45 else 0.0
        return Camera3D(x=0, y=0, z=120 + 110 * p, focal=900, shake_x=sh)
    scenes["alteration"] = (w_alt, cam_alt)

    # 5. Assassins (lunging paper puppet + raising dagger)
    w_ass = _make_plate_world("assassins")
    w_ass.add(Layer3D("assassin", _get("puppet_assassin", 500), x=-140, y=120, z=640,
                      scale=1.35, step_fps=12,
                      animate=lambda l, tl, tg: (
                          setattr(l, "x", -180 + tl * 85),
                          setattr(l, "z", 680 - tl * 45),
                      )))
    w_ass.add(Layer3D("dagger", _get("puppet_dagger_arm", 300), x=-40, y=40, z=610,
                      scale=1.15, pivot=(0.2, 0.8), step_fps=12,
                      animate=lambda l, tl, tg: (
                          setattr(l, "x", -80 + tl * 85),
                          setattr(l, "z", 650 - tl * 45),
                          setattr(l, "rot", -28 + 42 * min(1.0, tl / 2.2)),
                      )))
    def cam_ass(tl, dur):
        p = min(1.0, tl / max(0.1, dur))
        return Camera3D(x=-20 * p, y=0, z=90 * p, focal=900)
    scenes["assassins"] = (w_ass, cam_ass)

    # 6. Chase (jointed Narayanrao paper puppet running!)
    w_run = _make_plate_world("running")
    def _anim_torso(l, tl, tg):
        l.x = -260 + tl * 82
        l.y = 140 + 14 * abs(math.sin(tl * 11.0))
        l.rot = 8.0
    def _anim_head(l, tl, tg):
        l.x = -250 + tl * 82
        l.y = 15 + 14 * abs(math.sin(tl * 11.0))
        l.rot = -6.0 + 5.0 * math.sin(tl * 11.0)
    def _anim_leg_l(l, tl, tg):
        l.x = -260 + tl * 82
        l.y = 240 + 14 * abs(math.sin(tl * 11.0))
        l.rot = 36.0 * math.sin(tl * 11.0)
    def _anim_leg_r(l, tl, tg):
        l.x = -260 + tl * 82
        l.y = 240 + 14 * abs(math.sin(tl * 11.0))
        l.rot = -36.0 * math.sin(tl * 11.0)
    def _anim_arm(l, tl, tg):
        l.x = -255 + tl * 82
        l.y = 95 + 14 * abs(math.sin(tl * 11.0))
        l.rot = -32.0 * math.sin(tl * 11.0)

    w_run.add(Layer3D("boy_leg_r", _get("puppet_boy_leg", 300), z=635, scale=0.95, pivot=(0.5, 0.1), step_fps=12, animate=_anim_leg_r))
    w_run.add(Layer3D("boy_leg_l", _get("puppet_boy_leg", 300), z=625, scale=0.95, pivot=(0.5, 0.1), step_fps=12, animate=_anim_leg_l))
    w_run.add(Layer3D("boy_torso", _get("puppet_boy_torso", 350), z=620, scale=0.95, pivot=(0.5, 0.5), step_fps=12, animate=_anim_torso))
    w_run.add(Layer3D("boy_head", _get("puppet_boy_head", 250), z=615, scale=0.95, pivot=(0.5, 0.8), step_fps=12, animate=_anim_head))
    w_run.add(Layer3D("boy_arm", _get("puppet_boy_arm", 250), z=610, scale=0.95, pivot=(0.5, 0.1), step_fps=12, animate=_anim_arm))
    def cam_run(tl, dur):
        p = min(1.0, tl / max(0.1, dur))
        return Camera3D(x=-80 + 160 * p, y=0, z=60 * p, focal=900)
    scenes["chase"] = (w_run, cam_run)

    # 7. The Cry
    w_cry = _make_plate_world("hook")
    def cam_cry(tl, dur):
        p = min(1.0, tl / max(0.1, dur))
        sh = 14.0 * math.sin(tl * 50.0)
        return Camera3D(x=0, y=-30, z=150 + 100 * p, focal=900, shake_x=sh, shake_y=sh * 0.7)
    scenes["cry"] = (w_cry, cam_cry)

    # 8. Aftermath
    w_aft = _make_plate_world("courtyard")
    def cam_aft(tl, dur):
        p = min(1.0, tl / max(0.1, dur))
        return Camera3D(x=30 * p, y=10 * p, z=120 - 80 * p, focal=900)
    scenes["aftermath"] = (w_aft, cam_aft)

    # 9. River (moving paper waves + bobbing clay pot)
    w_riv = _make_plate_world("river")
    w_riv.add(Layer3D("wave_back", _get("prop_wave_1", 1200), x=0, y=260, z=720, scale=1.2, step_fps=12,
                      animate=lambda l, tl, tg: setattr(l, "x", -60 + 55 * math.sin(tl * 2.5))))
    w_riv.add(Layer3D("pot", _get("prop_pot", 250), x=-40, y=210, z=650, scale=1.05, step_fps=12,
                      animate=lambda l, tl, tg: (
                          setattr(l, "y", 210 + 18 * math.sin(tl * 3.8)),
                          setattr(l, "rot", 8.0 * math.cos(tl * 3.0)),
                      )))
    w_riv.add(Layer3D("wave_front", _get("prop_wave_1", 1200), x=40, y=340, z=560, scale=1.1, step_fps=12,
                      animate=lambda l, tl, tg: setattr(l, "x", 60 - 65 * math.sin(tl * 2.8))))
    def cam_riv(tl, dur):
        p = min(1.0, tl / max(0.1, dur))
        return Camera3D(x=0, y=20 * p, z=70 * p, focal=900)
    scenes["river"] = (w_riv, cam_riv)

    # 10. 1828 Fire (flickering paper flames)
    w_fire = _make_plate_world("fire")
    w_fire.add(Layer3D("flame_l", _get("prop_flame_1", 350), x=-220, y=180, z=640, scale=1.3, pivot=(0.5, 0.9), step_fps=12,
                       animate=lambda l, tl, tg: (
                           setattr(l, "sy", 1.0 + 0.22 * math.sin(tl * 13.0)),
                           setattr(l, "rot", 6.0 * math.cos(tl * 9.0)),
                       )))
    w_fire.add(Layer3D("flame_r", _get("prop_flame_2", 350), x=210, y=200, z=580, scale=1.25, pivot=(0.5, 0.9), step_fps=12,
                       animate=lambda l, tl, tg: (
                           setattr(l, "sy", 1.0 + 0.25 * math.cos(tl * 15.0)),
                           setattr(l, "rot", -7.0 * math.sin(tl * 10.0)),
                       )))
    def cam_fire(tl, dur):
        p = min(1.0, tl / max(0.1, dur))
        sh = 5.0 * math.sin(tl * 28.0)
        return Camera3D(x=0, y=-25 * p, z=95 * p, focal=900, shake_x=sh)
    scenes["fire"] = (w_fire, cam_fire)

    # 11. Legend (full moon + drifting cloud + ruins)
    w_leg = _make_plate_world("ruins")
    w_leg.add(Layer3D("moon_leg", _get("prop_moon", 400), x=-180, y=-480, z=1550, scale=1.15, shadow=False, step_fps=12))
    w_leg.add(Layer3D("cloud_leg", _get("prop_cloud", 600), x=180, y=-440, z=1380, scale=1.3, opacity=0.82, step_fps=12,
                      animate=lambda l, tl, tg: setattr(l, "x", 220 - tl * 45)))
    def cam_leg(tl, dur):
        p = min(1.0, tl / max(0.1, dur))
        return Camera3D(x=30 * p, y=-15 * p, z=80 * p, focal=900)
    scenes["legend"] = (w_leg, cam_leg)

    # 12. Doorway (shadowy figure looming)
    w_door = _make_plate_world("doorway")
    w_door.add(Layer3D("shadow_fig", _get("prop_shadow_figure", 550), x=0, y=40, z=700, scale=0.95, step_fps=12,
                       animate=lambda l, tl, tg: setattr(l, "z", 720 - tl * 16)))
    def cam_door(tl, dur):
        p = min(1.0, tl / max(0.1, dur))
        return Camera3D(x=0, y=0, z=140 * p, focal=900)
    scenes["doorway"] = (w_door, cam_door)

    return scenes
