# Pitch Slot Overflow Fix — Task Tracker

## Objective
Fix the coach dashboard tactical pitch so filled slots (photo + name + position) no longer
clip/overlap/overflow. Data and template logic are already correct — this is a pure CSS
layout problem.

## Status
- [x] Step 1: Enlarge desktop pitch + slots — `.pitch-wrap` max-width 780px, `aspect-ratio 3/2.2`
      (height ≈ 572px); `.pitch-slot` 96×88px.
- [x] Step 2: Tighten filled-slot labels — `.slot-pos` hidden (`display:none`) since the
      slot-key (e.g. "ST") already conveys position; freed vertical space.
- [x] Step 3: Name-overflow rule — desktop name is now a single-line pill with
      `white-space:nowrap; text-overflow:ellipsis` and a dark translucent background for
      legibility; no more 2-line clamp clipping.
- [x] Step 4: Mobile redesigned deliberately — slot 62×74px (larger than old 52×46px),
      avatar 34px (up from 26px), single-line truncated name; a genuine redesign, not a
      scaled-down copy.
- [x] Step 5: Avatar enlarged to 42px desktop for face recognizability.

## Verified Layout Math
- Slot content height (desktop): slot-key ~11px + avatar 45px + name ~19px + padding 8px
  ≈ 83px < 88px box height → no clipping.
- Worst-case vertical gap 16% (3-5-2) at 572px pitch ≈ 91.5px > 88px box → no vertical overlap.
- Worst-case horizontal gap 20% at 780px ≈ 156px > 96px box → no horizontal overlap.
- Mobile: slot-key 8px + avatar 34px + name 12px + padding 8px ≈ 62px < 74px box → fits.

## Files Edited
- `coach/templates/coach/coach_dashboard.html` (inline `<style>` block only)

## Follow-up (manual visual check)
- Load coach dashboard with a fully-populated formation (4-3-3 / 4-4-2 / 3-5-2).
- Confirm a no-photo player renders the fallback initial letter circle.
- Confirm a very long player name truncates with "…" instead of wrapping/overlapping.
