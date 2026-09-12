# TODO — Tournament Registration Flow

## Plan Steps

- [x] Step 1: Add `TournamentRegistration` model to `organizer/models.py` + migration
- [x] Step 2: Fix `Tournament.teams_count` to count approved registrations
- [x] Step 3: Decide URL placement (registration view lives in organizer app)
- [x] Step 4: Build `register_club_for_tournament` view in organizer
- [x] Step 5: Build "My Club's Registrations" view in clubs app
- [x] Step 6: Build organizer approval view
- [x] Step 7: Update templates (tournament_list + new templates)
- [x] Step 8: Update organizer_dashboard with pending count
- [x] Run make migrations (done), migrate (blocked- MySQL not running), py_compile validation (passed)

## League Scheduling Feature

- [x] Step 1: Added `Match` model with tournament/home_team/away_team, `match_date`, `status`, and the unique fixture constraint
- [x] Step 2: Added reusable round-robin generator in `matches/services.py`
- [x] Step 3: Added organizer-side safety gates before generation (`registration` status, existing schedule check, minimum approved teams)
- [x] Step 4: Added `generate_schedule` view and confirmation template
- [x] Step 5: Added `view_edit_schedule` view for assigning match dates
- [x] Step 6: Wired URLs for schedule generation and schedule editing
- [x] Step 7: Linked the schedule actions from the organizer tournament detail page
- [x] Step 8: Validated the Django project with `python manage.py check`

## Concurrency Fix

- [x] Added transaction-safe approval logic in `organizer/views.py` using `transaction.atomic()` and `select_for_update()`
- [x] Recomputed the approved registration count inside the lock before approving a club
- [x] Kept the reject flow unchanged and preserved the existing approval route contract

## Match Result Entry

- [x] Added `home_score` and `away_score` to the `Match` model.
- [x] Added `Goal`, `Card`, and `Substitution` models with club/player validation.
- [x] Generated and applied the migration for the score/result models.
- [x] Built organizer-only result entry view with score and event formsets.
- [x] Added match detail/read view for completed results.
- [x] Added Enter Result / View Result links from the schedule page.

## Current Status Update

- [x] Registration flow and approval logic are implemented in the real project folder.
- [x] Tournament list and manager dashboard navigation are wired to the correct routes.
- [x] League scheduling foundation is in place: round-robin generation, organizer safety checks, schedule generation, and edit page.
- [x] Match result entry and result reading are now implemented in the real project.
- [x] Django project validation passes with `python manage.py check`.
- [x] The active work is now reflected in the real project, not only in the worktree/session copy.

## Standings / Leaderboard

- [x] Built `standings/services.py`: `get_tournament_standings` computes points/goals from completed matches (3/1/0 scoring) with shared positions (1, 1, 3) and standard tiebreakers (points → GD → GF).
- [x] Added `get_club_standing(club, tournament)` helper returning a single club's row (position, points, played, W/D/L, GF/GA/GD).
- [x] Built public standings page (`standings/views.py`, template, URL) showing the full sorted table with leader/top-3 badges.
- [x] Added "My Standings" cards to the manager dashboard and coach dashboard (scoped to the club's own tournaments only).
- [x] Enriched dashboard standings with Played and Goal Difference (GF/GA/GD) alongside position/points/record.
- [x] Linked Standings from the organizer dashboard, tournament detail, and schedule pages.

## Organizer Dashboard Upgrades

- [x] Added upcoming matches and recent results cards (with live scores) to the organizer dashboard, merged into the stats row.
- [x] Fixed light-mode rendering on all organizer portal templates (`organizer_dashboard`, `approve_registrations`, `register_tournament`) with the same override the club dashboard uses.
- [x] Added Edit/Delete buttons to the organizer dashboard and tournament detail pages (danger-styled delete, TOCTOU-safe recheck before delete).
- [x] Added tournament edit and delete views/URLs/templates; delete confirm page shows a blocked state when the tournament has a schedule or has started.
- [x] Added `{% if messages %}` banners to organizer dashboard and tournament detail so success/error feedback is visible.

## Match Management

- [x] Added `cancel_match` / `uncancel_match` views (POST-only, ownership-gated) with three-state Actions column on the schedule page (Enter Result / Cancel, Cancelled pill + Uncancel, View Result).
- [x] Guarded `enter_match_result` against cancelled matches (blocked for both GET and POST).
- [x] Excluded cancelled matches from the organizer dashboard's upcoming matches query.
- [x] Added `{% if messages %}` banner to the schedule page.

## Match Result UI

- [x] Rewrote `match_detail.html` from Bootstrap classes (which the project does not load) to the native theme (scoreboard header, themed cards, status chips, messages banner).
- [x] Rewrote `generate_schedule.html` with the same theme (was also Bootstrap-based).
- [x] Split goals display by team on the read-only match detail page (home/away columns with counts).
- [x] Split the result entry form into team-scoped sections: two Goals sections, two Cards sections, and two Substitutions sections; each locks the team and filters player dropdowns to that club.
- [x] Added formset-level error display (`non_form_errors`) to the result entry page.

## Result Model Robustness

- [x] Guarded `Goal`/`Card`/`Substitution` model `clean()` against `RelatedObjectDoesNotExist` crashes when `match` is not yet assigned (ModelForm validation path).
- [x] Also guarded `Substitution.clean()` player-out/player-in FK accesses (partial-form crash of the same class).
- [x] Validated all features with `python manage.py check`, template compilation, and functional test-client smoke tests (in-memory SQLite).

