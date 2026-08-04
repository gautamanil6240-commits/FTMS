# Remove dead clubs.Player model & dead coach views

## Steps
- [x] 1. Verify clubs.Player.objects.count() == 0 (confirmed: 0)
- [x] 2. Remove CoachDashboardView and CoachAddPlayerView from clubs/views.py
- [x] 3. Update Player import in clubs/views.py to only import Club and Coach
- [x] 4. Remove dead URL patterns from clubs/urls.py
- [x] 5. Delete orphaned templates (coach_dashboard.html, add_player.html) — confirmed they do not exist
- [x] 6. Remove Player model from clubs/models.py
- [x] 7. Generate and review migration (makemigrations clubs) — 0004_delete_player.py
- [x] 8. Apply migration (migrate) — applied OK
- [x] 9. Wire up recent_players in ClubManagerDashboardView
- [x] 10. Adjust template field reference (position → preferred_position)
- [x] 11. Test full path end-to-end
