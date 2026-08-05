# Multi-Formation Feature — Task List

## Status Key
- [ ] Pending
- [x] Done

## Model & Migration
- [x] Step 1: Add `formation_type` to `Formation` (choices 4-3-3/4-4-2/3-5-2, default 4-3-3) + migrate.
- [x] Step 2: Add nullable `active_formation` FK to `Club` (SET_NULL) + migrate.
- [x] Step 3: Data-migrate existing `formation` → `active_formation`.
- [x] Step 4: Relax `Formation.club` OneToOne → ForeignKey (related_name='formations') + migrate.

## View & Logic
- [x] Step 5: Refactor `DEFAULT_433_SLOTS` → `FORMATION_TEMPLATES` dict (3 layouts) + `_create_formation(club, formation_type)` helper (no auto-assign).
- [x] Step 6: Rework lineup POST handling — picker creates/switches formation (empty, no auto-assign); dashboard reads `club.active_formation`.
- [x] Step 7: Scope `remove_player_from_roster` to active formation only (preserve historical snapshots).

## UI
- [x] Step 8: Add formation-type picker; render active formation's empty pitch for manual assignment.

## Testing
- [x] Step 9: Regression — build → assign → switch → history preserved → switch back → new row → unique constraint across formations; removed player only cleared from active formation.
- [x] Step 10: Cleanup temp files; `manage.py check` clean; update TODO.md.
