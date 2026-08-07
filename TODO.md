# TODO — Fix "cannot assign coach under manager" (User has no managed_club)

## Problem
- `managertest` (ID 4) has a `UserProfile` with `role='manager'` / `club_name='nepalFC'`,
  but no `Club` record links them as manager, so `request.user.managed_club` raises
  "User has no managed_club".
- Root cause: `accounts/views.py` `register()` creates a `UserProfile` for managers but
  never creates the corresponding `Club` model record (unlike `clubs.views.ClubManagerRegisterView`).

## Steps
- [x] 1. Investigate root cause (DB check + code analysis)
- [x] 2. Add `get_or_create_manager_club()` helper in `clubs/models.py` (auto-creates Club
       from UserProfile data when missing)
- [x] 3. Fix `accounts/views.py` `register()` to create a `Club` record when `role == 'manager'`
- [x] 4. Fix `accounts/views.py` `get_redirect_for_user()` & `user_login()` to auto-create Club
       for existing manager accounts
- [x] 5. Update `clubs/views.py` `ClubManagerDashboardView` & `AddCoachView` to use the helper
       and show a friendly error instead of raw debug text
- [x] 6. Create Club record for existing `managertest` account (via helper on next access / login)
- [x] 7. Test assign-coach flow (GET 200, POST 302, coach created & listed)

## Verification Results
- `get_or_create_manager_club(User(4))` → created `nepalFC` Club for `managertest`
- `user.managed_club` now returns the Club (no more "User has no managed_club")
- `/clubs/add-coach/` GET → 200 (form renders), POST → 302, coach user created & listed
- `/clubs/dashboard/` → 200, club name shown
- New manager registration via `accounts/register()` → creates both UserProfile and Club

