#!/usr/bin/env python3
"""sbar_check.py — validate the code-decoded bound-scrollbar geometry model.

Model source: doc 19 §7 (sbarRectsCompute 0x41DBD0, sbarHitTest 0x41E6B0,
sbarPressResolve 0x41E510, sbarValueFromPointer 0x41E5F0, sbarValueOffset
0x401700, scaleQuad 0x429C70). All formulas are executable-derived;
this tool checks their internal invariants (round-trips, clamps, minima,
degenerate cases) — it is NOT a rendering equivalence test.

Quad convention: corner form {x1, y1, x2, y2} (i16 values), CONFIRMED by
the degenerate checks in sbarRectsCompute/sldrRender and by the prvw
HOLD anchor geometry (sbvs = (250,110,266,236) -> 16x126 vertical strip;
sbhd = (10,30,350,46) -> 340x16 horizontal strip).

Rounding: x87 FISTP = round-half-to-even on the exact double value;
Python's round() on a float matches (ties-to-even on the binary double).

Part-descriptor model bytes (from a loaded appearance; all placeholder
values here — the real bytes come from the active appearance's parts):
  caps @+0x0C..+0x0F = capL, capT, capR, capB
  margins @+0x10..+0x13 = mL, mT, mR, mB
The min-size gate uses the SAME part descriptor's capL+capT in both
orientations (code: width/height CMP part+0x0C + part+0x0E).
"""

import sys

# ---------------------------------------------------------------- constants
DEFAULTS = dict(value=250, maxv=500, tn=50, td=100)  # sbarBindCreate defaults
# styleCtx metrics (runtime values = loaded appearance; plausible defaults):
MIN_THUMB_GLOBAL = 8      # styleCtx+0x98 (0x4669B4)
THUMB_ADD = 0             # styleCtx+0x9A (0x4669B6)
THRESHOLD = 24            # styleCtx+0x9C (0x4669B8): short-side threshold
CAPS = (8, 8, 8, 8)       # capL, capT, capR, capB @part+0x0C..+0x0F
MARGINS = (6, 4, 6, 4)    # mL, mT, mR, mB @part+0x10..+0x13
THUMB_CAPS = (6, 4, 6, 4) # thumb part caps


def fistp(d):
    """x87 FISTP: round-half-to-even to int."""
    return int(round(d))


def scale_quad(quad, num, den):
    """scaleQuad (0x429C70): dst[i] = (i32)(src[i] * num / den).
    C i32 division truncates toward zero (CDQ/IDIV)."""
    out = []
    for v in quad:
        p = v * num
        if den == 0:
            out.append(v)  # model-only guard (runtime den != 0)
        else:
            q = abs(p) // abs(den)
            out.append(q if p >= 0 else -q)
    return out


def floor_half(v):
    """SHR EAX,1 on a non-negative 32-bit value = floor(v/2)."""
    return v // 2


def rects(quad, value=250, maxv=500, tn=50, td=100,
          min_thumb_g=MIN_THUMB_GLOBAL, thumb_add=THUMB_ADD,
          threshold=THRESHOLD, caps=CAPS, margins=MARGINS,
          thumb_caps=THUMB_CAPS):
    """sbarRectsCompute (0x41DBD0). Returns a dict, or None if the rects
    were zeroed (nothing drawn)."""
    x1, y1, x2, y2 = quad
    w = x2 - x1
    h = y2 - y1
    if w <= 0 or h <= 0:
        return None  # degenerate quad -> out zeroed
    orient = 1 if w > h else 0  # 1 = horizontal
    capL, capT = caps[0], caps[1]
    if orient == 1:
        if h < threshold:  # narrow: single-band arrow cells
            if w < capL + capT:
                return None
            mL, mR = margins[0], margins[2]
            whole = (x1, y1, x1 + mL, y2)
            p1 = (x2 - mR, y1, x2, y2)
            p2 = p3 = (0, 0, 0, 0)
        else:  # wide: m/2 strip + m/2 inner band
            if w < capL + capT:
                return None
            mL, mR = margins[0], margins[2]
            whole = (x1, y1, x1 + floor_half(mL), y2)
            p1 = (x2 - floor_half(mR), y1, x2, y2)
            p2 = (x2 - mR, y1, x2 - floor_half(mR), y2)
            p3 = (x1 + floor_half(mL), y1, x1 + mL, y2)
        ts, te = x1 + mL, x2 - mR
    else:
        if h < capL + capT:  # min gate on the same part's capL+capT
            return None
        if w < threshold:  # narrow
            mT, mB = margins[1], margins[3]
            whole = (x1, y1, x2, y1 + mT)
            p1 = (x1, y2 - mB, x2, y2)
            p2 = p3 = (0, 0, 0, 0)
        else:  # wide
            mT, mB = margins[1], margins[3]
            whole = (x1, y1, x2, y1 + floor_half(mT))
            p1 = (x1, y2 - floor_half(mB), x2, y2)
            p2 = (x1, y2 - mB, x2, y2 - floor_half(mB))
            p3 = (x1, y1 + floor_half(mT), x2, y1 + mT)
        ts, te = y1 + mT, y2 - mB
    tmin = max(thumb_caps[0] + thumb_caps[1], min_thumb_g)

    track_len = te - ts
    if track_len < tmin + thumb_add:
        # thumb spans the whole track
        if orient == 1:
            return dict(orient=orient, whole=whole, p1=p1, p2=p2, p3=p3,
                        p4=(ts, y1, te, y2), p5=(0, 0, 0, 0), p6=(0, 0, 0, 0),
                        thumb_len=0, track_start=ts, track_end=te, full=True)
        return dict(orient=orient, whole=whole, p1=p1, p2=p2, p3=p3,
                    p4=(x1, ts, x2, te), p5=(0, 0, 0, 0), p6=(0, 0, 0, 0),
                    thumb_len=0, track_start=ts, track_end=te, full=True)

    tlen = fistp(track_len * tn / td) if td else track_len
    thumb_len = max(tlen, tmin)
    if value < maxv and maxv:
        pos = fistp((track_len - thumb_len) * value / maxv)
    else:
        pos = track_len - thumb_len
    t1 = ts + pos
    if orient == 1:
        p4, p5, p6 = ((ts, y1, t1, y2), (t1 + thumb_len, y1, te, y2),
                      (t1, y1, t1 + thumb_len, y2))
    else:
        p4, p5, p6 = ((x1, ts, x2, t1), (x1, t1 + thumb_len, x2, te),
                      (x1, t1, x2, t1 + thumb_len))
    return dict(orient=orient, whole=whole, p1=p1, p2=p2, p3=p3,
                p4=p4, p5=p5, p6=p6, thumb_len=thumb_len,
                track_start=ts, track_end=te, full=False)


def hit_test(r, px, py):
    """sbarHitTest (0x41E6B0): state 0..7, test order whole,p1,p2,p3,p4,p5,p6."""
    if r is None:
        return 0
    x1, y1, x2, y2 = r["whole"]
    if x1 <= px < x2 and y1 <= py < y2:
        return 1
    for st, k in ((2, "p1"), (3, "p2"), (4, "p3")):
        a, b, c, d = r[k]
        if (a or c) and a <= px < c and b <= py < d:
            return st
    a, b, c, d = r["p4"]
    if (a or c) and a <= px < c and b <= py < d:
        return 5
    a, b, c, d = r["p5"]
    if (a or c) and a <= px < c and b <= py < d:
        return 6
    a, b, c, d = r["p6"]
    if (a or c):
        if r["orient"] == 1:
            if x2 <= px < c and b <= py < d:  # whole.x2 <= px < thumb.x2
                return 7
        else:
            if y2 <= py < d and a <= px < c:  # whole.y2 <= py < thumb.y2
                return 7
    return 0


def value_from_pointer(r, quad, px, py, grab, maxv):
    """sbarValueFromPointer (0x41E5F0)."""
    if r is None:
        return 0
    if r["orient"] == 1:
        p, lo, hi = px - grab, r["p4"][0], r["p5"][2] - r["thumb_len"]
    else:
        p, lo, hi = py - grab, r["p4"][1], r["p5"][3] - r["thumb_len"]
    p = max(lo, min(p, hi))
    span = hi - lo
    if span <= 0:
        return maxv  # degenerate span: original falls to the "clamp up" path
    return fistp((p - lo) / span * maxv)


def thumb_pos(r):
    """thumb placement from the rects (p6 low edge)."""
    if r is None:
        return 0
    return r["p6"][0] if r["orient"] == 1 else r["p6"][1]


# ------------------------------------------------------------------ checks
FAILS = 0


def check(name, cond, detail=""):
    global FAILS
    if cond:
        print(f"  [ok  ] {name}" + (f" — {detail}" if detail else ""))
    else:
        FAILS += 1
        print(f"  [FAIL] {name}" + (f" — {detail}" if detail else ""))


def check_case(name, quad, **kw):
    print(f"\ncase: {name}  quad={tuple(quad)}")
    p = dict(DEFAULTS)
    p.update(kw)
    r = rects(quad, **p)
    if r is None:
        check("zeroed (not drawn)", True)
        return r
    check("orient flag sane", r["orient"] in (0, 1),
          "horizontal" if r["orient"] else "vertical")
    if not r["full"]:
        tl = r["thumb_len"]
        lo_i, hi_i = (0, 2) if r["orient"] == 1 else (1, 3)
        tmin = max(THUMB_CAPS[0] + THUMB_CAPS[1], p.get("min_thumb_g", MIN_THUMB_GLOBAL))
        check("thumb len >= minThumb", tl >= tmin, f"{tl} (min {tmin})")
        check("thumb inside track",
              r["p6"][lo_i] >= r["track_start"] and
              r["p6"][lo_i] + tl <= r["track_end"],
              f"thumb {r['p6'][lo_i]}..{r['p6'][lo_i] + tl} "
              f"in [{r['track_start']},{r['track_end']}]")
        check("p4/p5/p6 chain contiguous",
              r["p4"][lo_i] == r["track_start"] and
              r["p4"][hi_i] == r["p6"][lo_i] and
              r["p6"][lo_i] + tl == r["p5"][lo_i] and
              r["p5"][hi_i] == r["track_end"])
        # round-trip: value -> pixel -> value. The forward map quantizes
        # (pos = FISTP(span * v/max)), so the inverse can drift by at most
        # one pixel worth of value — this is a property of the original,
        # not a model error.
        v = p["value"]
        pos = thumb_pos(r)
        span = r["track_end"] - tl - r["track_start"]
        if r["orient"] == 1:
            cx, cy = pos + tl // 2, (quad[1] + quad[3]) // 2
        else:
            cx, cy = (quad[0] + quad[2]) // 2, pos + tl // 2
        v2 = value_from_pointer(r, quad, cx, cy, tl // 2, p["maxv"])
        tol = p["maxv"] // max(span, 1) + 1 if span > 0 else 0
        check("round-trip value->pos->value (±1px quantization)",
              abs(v2 - v) <= tol, f"{v} -> {v2} (tol {tol})")
        # pointer clamps
        BIG = 10 ** 6
        if r["orient"] == 1:
            vmax = value_from_pointer(r, quad, BIG, cy, 0, p["maxv"])
            vmin = value_from_pointer(r, quad, -BIG, cy, 0, p["maxv"])
        else:
            vmax = value_from_pointer(r, quad, cx, BIG, 0, p["maxv"])
            vmin = value_from_pointer(r, quad, cx, -BIG, 0, p["maxv"])
        check("pointer past end -> value=max", vmax == p["maxv"], f"{vmax}")
        check("pointer past start -> value=0", vmin == 0, f"{vmin}")
        # endpoint snapping
        r0 = rects(quad, value=0, maxv=p["maxv"], tn=p["tn"], td=p["td"],
                   min_thumb_g=p.get("min_thumb_g", MIN_THUMB_GLOBAL),
                   thumb_add=p.get("thumb_add", THUMB_ADD),
                   threshold=p.get("threshold", THRESHOLD),
                   caps=p.get("caps", CAPS), margins=p.get("margins", MARGINS),
                   thumb_caps=p.get("thumb_caps", THUMB_CAPS))
        rm = rects(quad, value=p["maxv"], maxv=p["maxv"], tn=p["tn"],
                   td=p["td"], min_thumb_g=p.get("min_thumb_g", MIN_THUMB_GLOBAL),
                   thumb_add=p.get("thumb_add", THUMB_ADD),
                   threshold=p.get("threshold", THRESHOLD),
                   caps=p.get("caps", CAPS), margins=p.get("margins", MARGINS),
                   thumb_caps=p.get("thumb_caps", THUMB_CAPS))
        check("value=0 -> thumb at trackStart",
              r0 and thumb_pos(r0) == r0["track_start"])
        check("value=max -> thumb at trackEnd-thumbLen",
              rm and thumb_pos(rm) + rm["thumb_len"] == rm["track_end"])
        # hit test: thumb center must be state 7
        st = hit_test(r, cx, cy)
        check("thumb center hit-test = state 7", st == 7, f"state {st}")
    return r


def main():
    print("sbar_check — bound-scrollbar geometry invariants")
    print("(model: doc 19 §7; formulas executable-derived)")

    print("\n--- degenerate inputs")
    check("zero-width quad -> zeroed", rects((100, 10, 100, 40)) is None)
    check("zero-height quad -> zeroed", rects((10, 10, 10, 40)) is None)
    check("w < part.capL+capT -> zeroed (horizontal)",
          rects((10, 10, 24, 14)) is None, "w=14 > h=4 (horizontal), 14 < 8+8")
    check("h < part.capL+capT -> zeroed (vertical)",
          rects((10, 10, 14, 24)) is None, "h=14 > w=4 (vertical), 14 < 8+8")

    print("\n--- scaleQuad (i32 truncate-toward-zero multiply-divide)")
    q = (10, 30, 350, 46)
    check("scale 1:1 identity", scale_quad(q, 100, 100) == list(q))
    check("scale 3:4 positive truncation",
          scale_quad((1, 0, 9, 0), 3, 4) == [0, 0, 6, 0],
          str(scale_quad((1, 0, 9, 0), 3, 4)))
    check("scale 3:4 negative truncates toward zero",
          scale_quad((-1, 0, -9, 0), 3, 4) == [0, 0, -6, 0],
          str(scale_quad((-1, 0, -9, 0), 3, 4)))
    check("scale 2:1 doubles", scale_quad(q, 2, 1) == [20, 60, 700, 92])
    for num, den in ((75, 100), (50, 100), (125, 100), (67, 100)):
        s = scale_quad(q, num, den)
        check(f"scale {num}:{den} stays non-degenerate",
              s[2] > s[0] and s[3] > s[1], str(tuple(s)))

    print("\n--- horizontal scrollbars (prvw-style anchors, corner form)")
    check_case("sbhd default (250/500)", (10, 30, 350, 46))
    check_case("sbhd value=0", (10, 30, 350, 46), value=0)
    check_case("sbhd value=max", (10, 30, 350, 46), value=500)
    check_case("sbhd value=137", (10, 30, 350, 46), value=137)
    check_case("sbhd zero range (value==max)", (10, 30, 350, 46),
               value=500, maxv=500)
    check_case("sbhd scaled 75%", tuple(scale_quad((10, 30, 350, 46), 75, 100)))
    check_case("sbhd scaled 50%", tuple(scale_quad((10, 30, 350, 46), 50, 100)))
    check_case("sbhd scaled 125%", tuple(scale_quad((10, 30, 350, 46), 125, 100)))

    print("\n--- vertical scrollbars")
    check_case("sbvs default", (250, 110, 266, 236))
    check_case("sbvs value=0", (250, 110, 266, 236), value=0)
    check_case("sbvs value=max", (250, 110, 266, 236), value=500)
    check_case("sbvs value=333", (250, 110, 266, 236), value=333)
    check_case("sbvs scaled 75%", tuple(scale_quad((250, 110, 266, 236), 75, 100)))

    print("\n--- small control dimensions")
    check_case("near-min track", (0, 0, 40, 20), min_thumb_g=10)
    r = check_case("degenerate track (full-thumb mode)", (0, 0, 30, 20),
                   min_thumb_g=20, thumb_add=5)
    if r:
        check("full-thumb mode: p5/p6 zero",
              r["p5"] == (0, 0, 0, 0) and r["p6"] == (0, 0, 0, 0))
        check("full-thumb mode: p4 = whole track",
              r["p4"][0] == r["track_start"] and r["p4"][2] == r["track_end"])

    print("\n--- adaptive arrow disappearance (narrow vs wide)")
    r_n = rects((0, 0, 200, 12), threshold=24)   # h=12 < 24 -> narrow
    r_w = rects((0, 0, 200, 30), threshold=24)   # h=30 >= 24 -> wide
    check("narrow: part2/part3 zero",
          r_n["p2"] == (0, 0, 0, 0) and r_n["p3"] == (0, 0, 0, 0))
    check("wide: part2/part3 non-zero strips",
          r_w["p2"][2] > r_w["p2"][0] and r_w["p3"][2] > r_w["p3"][0])
    check("narrow: whole spans full cap margin",
          r_n["whole"][2] - r_n["whole"][0] == MARGINS[0],
          f"{r_n['whole'][2] - r_n['whole'][0]} (mL={MARGINS[0]})")
    check("wide: whole spans half cap margin",
          r_w["whole"][2] - r_w["whole"][0] == floor_half(MARGINS[0]),
          f"{r_w['whole'][2] - r_w['whole'][0]} (mL={MARGINS[0]})")

    print("\n--- thumb minimums")
    r_big = rects((0, 0, 400, 30), tn=1, td=1000, min_thumb_g=24)
    check("tiny ratio clamped to minThumb",
          r_big is not None and r_big["thumb_len"] == 24,
          f"{r_big and r_big['thumb_len']}")

    print("\n--- rounding (FISTP ties-to-even)")
    check("fistp(0.5)=0", fistp(0.5) == 0)
    check("fistp(1.5)=2", fistp(1.5) == 2)
    check("fistp(2.5)=2", fistp(2.5) == 2)
    check("fistp(2.9)=3", fistp(2.9) == 3)
    check("fistp(-2.5)=-2", fistp(-2.5) == -2)

    print()
    if FAILS:
        print(f"RESULT: {FAILS} FAILURES")
        return 1
    print("RESULT: ALL OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
