# Lineup/Formation Feature — Improvement Tasks

## Status Key
- [ ] Pending
- [x] Done

## Data Integrity
- [x] Item 1: `LineupSlot.player` already uses `on_delete=SET_NULL, null=True` — verified correct, no change needed.
- [x] Item 2: Add DB-level `UniqueConstraint(fields=['formation', 'player'])` to prevent one player in two slots.
  - **Note:** Revised to a **plain (unconditional)** unique constraint. The original `condition=Q(player__isnull=False)` version is **not supported by MariaDB** (Django model W036 — silently skipped, so the constraint was never created despite migration 0006 being marked applied). A plain unique constraint achieves the same behavior on MariaDB/Postgres/SQLite because NULL values are always distinct in unique indexes (unlimited empty slots allowed, duplicate non-null player rejected). Migration `0007` removes the broken conditional constraint and re-creates it as a plain one; verified present in `information_schema` as a real `UNIQUE` constraint.

## Business Logic
- [x] Item 3: Add "Bench / Unassigned" list (roster players not in any slot).
- [x] Item 4: Add `auto_assigned` flag + "Auto-assigned" indicator on slots.

## Security
- [x] Item 6: `build_formation` already derives club from session — verified correct, no change needed.

## Visual / UX Polish
- [x] Item 7: Add circular player-photo thumbnails to filled slots.
- [x] Item 8: Improve mobile responsiveness of slot cards (smaller cards / abbreviated labels).

## Extensibility
- [ ] Item 9: Coordinates baked into DB at creation — known limitation, data migration needed later.
- [x] Item 10: Multi-formation support — **implemented** (see `TODO_multi_formation.md`). `Formation` is now a `ForeignKey` to Club (relaxed from OneToOne), clubs get a nullable `active_formation` FK, and a picker lets coaches switch between 4-3-3 / 4-4-2 / 3-5-2. Every switch creates a fresh empty formation row (no auto-assign), preserving prior lineups as immutable historical snapshots. 17/17 regression tests pass.

## Verification Steps
- [x] Run `python manage.py makemigrations coach` — "No changes detected," then generated 0007 for the constraint revision.
- [x] Run `python manage.py migrate` — applied 0007 cleanly; W036 warning gone; `unique_player_per_formation` confirmed present in `information_schema` as a real `UNIQUE` constraint.
- [x] Verify no model/DB errors — `python manage.py check` reports no issues (0 silenced).

## Item 5 — preferred_position ↔ position_hint mapping (was dropped from list)
- [x] Verified: distinct `preferred_position` values currently in DB are `['defender', 'forward', 'goalkeeper']` — all map cleanly to the four `POSITION_HINTS` categories (goalkeeper/defender/midfielder/forward). No fine-grained values (e.g. "Right Winger") exist, so the smart-defaults auto-assignment works correctly. **No code change needed** — logged here so it's not silently skipped.

## End-to-End Regression Test (added this session)
- [x] Wrote and ran a model-level regression test against the real DB — **13/13 passed**:
  - Auto-assignment places players by position and sets `auto_assigned=True` on the filled slots only.
  - Manually moving a player to another slot clears the old slot (moved, not duplicated).
  - The DB-level `unique_player_per_formation` constraint rejects a duplicate assignment (confirmed working on MariaDB).
  - Removing a player from the roster clears their lineup slot (slot survives, player→NULL).
  - Bench list updates correctly as players are assigned/cleared.
- [x] **Bug found & fixed:** `remove_player_from_roster` set `player.club = None` but did **not** clear the lineup slot, so a player removed from the squad would still appear on the pitch. Fixed by wrapping the removal in `transaction.atomic()` and clearing any `LineupSlot` rows for that player (with `auto_assigned=False`) before nulling the club. (SET_NULL only fires on player deletion, not on setting club to null.)
- [x] **Mobile responsiveness (Item 8):** Confirmed the `@media (max-width: 600px)` block in `coach_dashboard.html` shrinks slot cards (52×46px) and avatars (26px) with shorter labels — handles longer player names. Also `@media (max-width: 900px)` stacks the bench layout. Verified in code; visual check on a narrow viewport still recommended.
- [x] Temp verification scripts (`check_constraints.py`, `verify_constraint.py`, `regression_test.py`) created during verification and removed.

## IntegrityError race-condition handling in `assign_slot` (verified, not just reviewed)
- [x] Confirmed the `assign_slot` view catches `IntegrityError` inside `transaction.atomic()` and returns a **clean redirect** (302, not a 500) with the friendly message `"{player} was just assigned elsewhere — please try again."`
- [x] Verified with a focused test that simulates the DB `unique_player_per_formation` constraint firing under a race (forced `IntegrityError` on save):
  - Normal assignment → 302, player placed correctly.
  - Forced race/constraint violation → **302 redirect** (no 500) with the friendly re-try message.
  - Atomic rollback preserved the original assignment (failed slot stayed empty).
- [x] Temp script (`test_integrity_error.py`) created for this and removed.

## Light-theme fix — role-login-selection page (`login_selection.html`)
- [x] Fixed "Viewer" / "Watch tournaments" (and other role card text) blending into the background on light theme: added light-mode overrides (inline in the template `<style>` + in `login_selection.css`) so role cards render white with dark text and readable buttons.
- [x] Preserved the `role.png` background image in light mode — it is lightened with a white scrim (`rgba(255,255,255,0.78–0.82)`) rather than replaced, so the original background design is kept while text stays readable. Dark mode is unchanged.
