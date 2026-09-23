# TODO — FTMS Project Trackers

All feature trackers are consolidated into this file.

---

## 1. Tournament Registration Flow

### Plan Steps
- [x] Step 1: Add `TournamentRegistration` model to `organizer/models.py` + migration
- [x] Step 2: Fix `Tournament.teams_count` to count approved registrations
- [x] Step 3: Decide URL placement (registration view lives in organizer app)
- [x] Step 4: Build `register_club_for_tournament` view in organizer
- [x] Step 5: Build "My Club's Registrations" view in clubs app
- [x] Step 6: Build organizer approval view
- [x] Step 7: Update templates (tournament_list + new templates)
- [x] Step 8: Update organizer_dashboard with pending count
- [x] Run make migrations (done), migrate (blocked- MySQL not running), py_compile validation (passed)

---

## 2. League Scheduling Feature

- [x] Step 1: Added `Match` model with tournament/home_team/away_team, `match_date`, `status`, and the unique fixture constraint
- [x] Step 2: Added reusable round-robin generator in `matches/services.py`
- [x] Step 3: Added organizer-side safety gates before generation (`registration` status, existing schedule check, minimum approved teams)
- [x] Step 4: Added `generate_schedule` view and confirmation template
- [x] Step 5: Added `view_edit_schedule` view for assigning match dates
- [x] Step 6: Wired URLs for schedule generation and schedule editing
- [x] Step 7: Linked the schedule actions from the organizer tournament detail page
- [x] Step 8: Validated the Django project with `python manage.py check`

---

## 3. Concurrency Fix

- [x] Added transaction-safe approval logic in `organizer/views.py` using `transaction.atomic()` and `select_for_update()`
- [x] Recomputed the approved registration count inside the lock before approving a club
- [x] Kept the reject flow unchanged and preserved the existing approval route contract

---

## 4. Match Result Entry

- [x] Added `home_score` and `away_score` to the `Match` model.
- [x] Added `Goal`, `Card`, and `Substitution` models with club/player validation.
- [x] Generated and applied the migration for the score/result models.
- [x] Built organizer-only result entry view with score and event formsets.
- [x] Added match detail/read view for completed results.
- [x] Added Enter Result / View Result links from the schedule page.

---

## 5. Current Status Update

- [x] Registration flow and approval logic are implemented in the real project folder.
- [x] Tournament list and manager dashboard navigation are wired to the correct routes.
- [x] League scheduling foundation is in place: round-robin generation, organizer safety checks, schedule generation, and edit page.
- [x] Match result entry and result reading are now implemented in the real project.
- [x] Django project validation passes with `python manage.py check`.
- [x] The active work is now reflected in the real project, not only in the worktree/session copy.

---

## 6. Standings / Leaderboard

- [x] Built `standings/services.py`: `get_tournament_standings` computes points/goals from completed matches (3/1/0 scoring) with shared positions (1, 1, 3) and standard tiebreakers (points → GD → GF).
- [x] Added `get_club_standing(club, tournament)` helper returning a single club's row (position, points, played, W/D/L, GF/GA/GD).
- [x] Built public standings page (`standings/views.py`, template, URL) showing the full sorted table with leader/top-3 badges.
- [x] Added "My Standings" cards to the manager dashboard and coach dashboard (scoped to the club's own tournaments only).
- [x] Enriched dashboard standings with Played and Goal Difference (GF/GA/GD) alongside position/points/record.
- [x] Linked Standings from the organizer dashboard, tournament detail, and schedule pages.

---

## 7. Organizer Dashboard Upgrades

- [x] Added upcoming matches and recent results cards (with live scores) to the organizer dashboard, merged into the stats row.
- [x] Fixed light-mode rendering on all organizer portal templates (`organizer_dashboard`, `approve_registrations`, `register_tournament`) with the same override the club dashboard uses.
- [x] Added Edit/Delete buttons to the organizer dashboard and tournament detail pages (danger-styled delete, TOCTOU-safe recheck before delete).
- [x] Added tournament edit and delete views/URLs/templates; delete confirm page shows a blocked state when the tournament has a schedule or has started.
- [x] Added `{% if messages %}` banners to organizer dashboard and tournament detail so success/error feedback is visible.

---

## 8. Match Management

- [x] Added `cancel_match` / `uncancel_match` views (POST-only, ownership-gated) with three-state Actions column on the schedule page (Enter Result / Cancel, Cancelled pill + Uncancel, View Result).
- [x] Guarded `enter_match_result` against cancelled matches (blocked for both GET and POST).
- [x] Excluded cancelled matches from the organizer dashboard's upcoming matches query.
- [x] Added `{% if messages %}` banner to the schedule page.

---

## 9. Match Result UI

- [x] Rewrote `match_detail.html` from Bootstrap classes (which the project does not load) to the native theme (scoreboard header, themed cards, status chips, messages banner).
- [x] Rewrote `generate_schedule.html` with the same theme (was also Bootstrap-based).
- [x] Split goals display by team on the read-only match detail page (home/away columns with counts).
- [x] Split the result entry form into team-scoped sections: two Goals sections, two Cards sections, and two Substitutions sections; each locks the team and filters player dropdowns to that club.
- [x] Added formset-level error display (`non_form_errors`) to the result entry page.

---

## 10. Result Model Robustness

- [x] Guarded `Goal`/`Card`/`Substitution` model `clean()` against `RelatedObjectDoesNotExist` crashes when `match` is not yet assigned (ModelForm validation path).
- [x] Also guarded `Substitution.clean()` player-out/player-in FK accesses (partial-form crash of the same class).
- [x] Validated all features with `python manage.py check`, template compilation, and functional test-client smoke tests (in-memory SQLite).

---

## 11. New Tournament Fields (Model/Form/Template Enhancements)

- [x] Analyze repository (models, forms, views, templates, migrations)
- [x] 1. Add new fields to `organizer/models.py` (registration_type, contact_person, phone, registration_deadline, age_category, gender_category, award fields)
- [x] 2. Update `organizer/forms.py` to include new fields + validation
- [x] 3. Update `organizer/views.py` for status filtering in tournament_list
- [x] 4. Update `organizer/templates/organizer/create_tournament.html` (status choices, registration_type)
- [x] 5. Update `organizer/templates/organizer/tournament_detail.html` (display new fields)
- [x] 6. Update `organizer/templates/organizer/tournament_list.html` (replace ongoing with active)
- [x] 7. Run `makemigrations` (migration `0002_tournament_age_category_and_more.py` created)
- [ ] 8. Run `migrate` (⚠️ requires MySQL server running — currently not connected)
- [x] 9. Run `manage.py check` (no issues)

**Notes:**
- Project DB is MySQL (`ftms_db` on localhost:3306). MySQL server was not running during migration generation.
- To apply the migration, start MySQL then run: `python manage.py migrate organizer`

---

## 12. Multi-Formation Feature

### Model & Migration
- [x] Step 1: Add `formation_type` to `Formation` (choices 4-3-3/4-4-2/3-5-2, default 4-3-3) + migrate.
- [x] Step 2: Add nullable `active_formation` FK to `Club` (SET_NULL) + migrate.
- [x] Step 3: Data-migrate existing `formation` → `active_formation`.
- [x] Step 4: Relax `Formation.club` OneToOne → ForeignKey (related_name='formations') + migrate.

### View & Logic
- [x] Step 5: Refactor `DEFAULT_433_SLOTS` → `FORMATION_TEMPLATES` dict (3 layouts) + `_create_formation(club, formation_type)` helper (no auto-assign).
- [x] Step 6: Rework lineup POST handling — picker creates/switches formation (empty, no auto-assign); dashboard reads `club.active_formation`.
- [x] Step 7: Scope `remove_player_from_roster` to active formation only (preserve historical snapshots).

### UI
- [x] Step 8: Add formation-type picker; render active formation's empty pitch for manual assignment.

### Testing
- [x] Step 9: Regression — build → assign → switch → history preserved → switch back → new row → unique constraint across formations; removed player only cleared from active formation.
- [x] Step 10: Cleanup temp files; `manage.py check` clean; update TODO.md.

---

## 13. Pitch Slot Overflow Fix

**Objective:** Fix the coach dashboard tactical pitch so filled slots (photo + name + position) no longer clip/overlap/overflow. Data and template logic are already correct — this is a pure CSS layout problem.

- [x] Step 1: Enlarge desktop pitch + slots — `.pitch-wrap` max-width 780px, `aspect-ratio 3/2.2` (height ≈ 572px); `.pitch-slot` 96×88px.
- [x] Step 2: Tighten filled-slot labels — `.slot-pos` hidden (`display:none`) since the slot-key (e.g. "ST") already conveys position; freed vertical space.
- [x] Step 3: Name-overflow rule — desktop name is now a single-line pill with `white-space:nowrap; text-overflow:ellipsis` and a dark translucent background for legibility; no more 2-line clamp clipping.
- [x] Step 4: Mobile redesigned deliberately — slot 62×74px (larger than old 52×46px), avatar 34px (up from 26px), single-line truncated name; a genuine redesign, not a scaled-down copy.
- [x] Step 5: Avatar enlarged to 42px desktop for face recognizability.

### Verified Layout Math
- Slot content height (desktop): slot-key ~11px + avatar 45px + name ~19px + padding 8px ≈ 83px < 88px box height → no clipping.
- Worst-case vertical gap 16% (3-5-2) at 572px pitch ≈ 91.5px > 88px box → no vertical overlap.
- Worst-case horizontal gap 20% at 780px ≈ 156px > 96px box → no horizontal overlap.
- Mobile: slot-key 8px + avatar 34px + name 12px + padding 8px ≈ 62px < 74px box → fits.

### Files Edited
- `coach/templates/coach/coach_dashboard.html` (inline `<style>` block only)

### Follow-up (manual visual check)
- Load coach dashboard with a fully-populated formation (4-3-3 / 4-4-2 / 3-5-2).
- Confirm a no-photo player renders the fallback initial letter circle.
- Confirm a very long player name truncates with "…" instead of wrapping/overlapping.

---

## 14. Read-Only Tactics on Manager & Player Dashboards

**Objective:** Show the club's current active formation (tactical lineup) read-only on the manager dashboard and the player dashboard. No new save mechanism needed — `Club.active_formation` already exists and is updated by the coach. Just read & render.

- [x] Step 1: Add a single shared helper to fetch a club's active_formation + slots (generic, no player-specific logic).
- [x] Step 2: Manager view — add formation + lineup_slots to context via shared helper.
- [x] Step 3: Manager template — add full-width "🎯 Tactics" section below the split layout, neutral non-interactive pitch (no data-slot-id, no modal JS, no "+ Add").
- [x] Step 4: Manager empty state — "No tactics set yet — your coach hasn't built a lineup."
- [x] Step 5: Player view — add formation, lineup_slots, my_slot to context; remove the duplicate dead `player_dashboard` function.
- [x] Step 6: Player template — add prominent "🎯 My Lineup" section near top (after profile-card): "You're starting at X" / "not in lineup" / "no tactics" / distinct free-agent message; highlight own slot with "You" badge.
- [x] Step 7: Add pitch CSS to both templates.
- [x] Step 8: Verify club-scoping via request.user relationships only (no URL params).
- [x] Step 9: Verify full scenario matrix.

**Info:**
- Club relation: `request.user.managed_club` (manager), `player.club` (player).
- Shared helper lives in `coach/models.py` (referenced by both clubs & players apps).
- No migrations needed (no schema change).

---

## Open Items

- [ ] Run `python manage.py migrate organizer` once MySQL (`ftms_db`, localhost:3306) is running.
