# Data migration: for every Club that has existing Formation rows, set
# club.active_formation to the first (previously the sole OneToOne) formation.
# Before this change, Formation.club was OneToOne, so each club had at most one
# formation. After the FK relax (coach/0008), a club may have many Formation
# rows; we pick the one that was previously linked.

from django.db import migrations


def populate_active_formation(apps, schema_editor):
    Club = apps.get_model('clubs', 'Club')
    Formation = apps.get_model('coach', 'Formation')
    for club in Club.objects.all():
        formation = Formation.objects.filter(club=club).order_by('-updated_at').first()
        if formation:
            club.active_formation = formation
            club.save(update_fields=['active_formation'])


def unpopulate_active_formation(apps, schema_editor):
    Club = apps.get_model('clubs', 'Club')
    Club.objects.update(active_formation=None)


class Migration(migrations.Migration):

    dependencies = [
        ('clubs', '0005_club_active_formation'),
        ('coach', '0008_formation_formation_type_alter_formation_club'),
    ]

    operations = [
        migrations.RunPython(populate_active_formation, unpopulate_active_formation),
    ]
