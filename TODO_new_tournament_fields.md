# TODO: Tournament Model/Form/Template Enhancements

## Steps
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

## Notes
- Project DB is MySQL (`ftms_db` on localhost:3306). MySQL server was not running during migration generation.
- To apply the migration, start MySQL then run: `python manage.py migrate organizer`
