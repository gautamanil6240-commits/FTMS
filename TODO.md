# Coach Cannot View Player Profile from Squad Roster - Fix TODO

## Problem
The coach dashboard "View Profile" link uses `{% url 'coach:player_detail_pk' player.id %}` (auto-increment PK). But in `coach/urls.py`, the `<str:player_id>` pattern is declared BEFORE `<int:pk>`, so Django's `<str:player_id>` route intercepts `/player/5/` and tries `Player.objects.get(player_id='5')` — which looks up the 6-digit code, not the PK → 404.

## Steps
- [x] 1. Fix `coach/templates/coach/coach_dashboard.html` — "View Profile" link → use `{% url 'coach:player_detail' player.player_id %}` (6-digit code, str route)
- [x] 2. Update `coach/views.py` — `player_detail_view` → add POST handling for `add_performance` (modal on the str-route profile page)
- [x] 3. Update `coach/views.py` — `_log_performance` → redirect to `coach:player_detail` with `player.player_id` instead of `player_detail_pk`
- [x] 4. Verify with `python manage.py check` (passed, no issues)
- [x] 5. Verified URL routing in shell: `reverse('coach:player_detail', args=[player.player_id])` → `/coach/player/70e4a7/`, resolves to `player_detail_view`

