# TODO: Make auth pages theme-aware (fix login box staying dark in light theme)

## Approach
- Added two new theme-aware CSS variables in `base.css`:
  - `--auth-overlay-a` / `--auth-overlay-b` (dark defaults) and light-mode overrides.
- Replaced all hardcoded `rgba(0,0,0,...)` dark gradients in auth templates with these variables.

## Steps
- [x] 1. `base.css` — add `--auth-overlay-a/b` variables (dark + light)
- [x] 2. `login.html` — replace hardcoded dark gradient with theme-aware overlays
- [x] 3. `login_selection.html` — replace hardcoded dark gradient with theme-aware overlays
- [x] 4. `register_base.html` — replace hardcoded dark gradient with theme-aware overlays
- [x] 5. `register.css` — used by `register.html`, replace hardcoded dark gradient with theme-aware overlays
- [x] 6. `register_organizer.html` — replace hardcoded dark gradient with theme-aware overlays
- [x] 7. `register_player.html` — replace hardcoded dark gradient with theme-aware overlays
- [x] 8. `register_coach.html` — replace hardcoded dark gradient with theme-aware overlays
- [x] 9. `register_manager.html` — replace hardcoded dark gradient with theme-aware overlays
- [x] 10. `register_viewer.html` — replace hardcoded dark gradient with theme-aware overlays
- [x] 11. `already_logged_in.html` — replace hardcoded dark gradient with theme-aware overlays
- [ ] 12. Verify by toggling theme on login page
