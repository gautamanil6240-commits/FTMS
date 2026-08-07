# Read-Only Tactics on Manager & Player Dashboards — Task Tracker

## Objective
Show the club's current active formation (tactical lineup) read-only on the manager
dashboard and the player dashboard. No new save mechanism needed — `Club.active_formation`
already exists and is updated by the coach. Just read & render.

## Steps
- [x] Step 1: Add a single shared helper to fetch a club's active_formation + slots
      (generic, no player-specific logic).
- [x] Step 2: Manager view — add formation + lineup_slots to context via shared helper.
- [x] Step 3: Manager template — add full-width "🎯 Tactics" section below the split
      layout, neutral non-interactive pitch (no data-slot-id, no modal JS, no "+ Add").
- [x] Step 4: Manager empty state — "No tactics set yet — your coach hasn't built a lineup."
- [x] Step 5: Player view — add formation, lineup_slots, my_slot to context; remove the
      duplicate dead `player_dashboard` function.
- [x] Step 6: Player template — add prominent "🎯 My Lineup" section near top (after
      profile-card): "You're starting at X" / "not in lineup" / "no tactics" / distinct
      free-agent message; highlight own slot with "You" badge.
- [x] Step 7: Add pitch CSS to both templates.
- [x] Step 8: Verify club-scoping via request.user relationships only (no URL params).
- [x] Step 9: Verify full scenario matrix.

## Info
- Club relation: `request.user.managed_club` (manager), `player.club` (player).
- Shared helper lives in `coach/models.py` (referenced by both clubs & players apps).
- No migrations needed (no schema change).
