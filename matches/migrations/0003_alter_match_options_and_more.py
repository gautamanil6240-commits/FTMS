# Migration 0003: Add bracket fields, nullable teams, remove unique constraint.
# Uses RunPython to handle MariaDB FK-index dependency dynamically.

from django.db import migrations, models
import django.db.models.deletion


def drop_unique_constraint_forwards(apps, schema_editor):
    """Drop unique_tournament_fixture on MariaDB where FK indexes block direct removal."""
    table = 'matches_match'

    # Find all FK constraints on this table
    with schema_editor.connection.cursor() as cursor:
        cursor.execute(
            "SELECT CONSTRAINT_NAME FROM information_schema.TABLE_CONSTRAINTS "
            "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = %s "
            "AND CONSTRAINT_TYPE = 'FOREIGN KEY'",
            [table],
        )
        fk_names = [row[0] for row in cursor.fetchall()]

    # Drop each FK constraint
    for fk_name in fk_names:
        schema_editor.execute(
            f"ALTER TABLE {table} DROP FOREIGN KEY `{fk_name}`"
        )

    # Now safe to drop the unique index
    schema_editor.execute(
        f"ALTER TABLE {table} DROP INDEX unique_tournament_fixture"
    )

    # Re-add FK constraints so Django's state stays consistent
    schema_editor.execute(
        f"ALTER TABLE {table} "
        f"ADD CONSTRAINT matches_match_home_team_id_fk "
        f"FOREIGN KEY (home_team_id) REFERENCES clubs_club(id) ON DELETE CASCADE"
    )
    schema_editor.execute(
        f"ALTER TABLE {table} "
        f"ADD CONSTRAINT matches_match_away_team_id_fk "
        f"FOREIGN KEY (away_team_id) REFERENCES clubs_club(id) ON DELETE CASCADE"
    )


def drop_unique_constraint_reverse(apps, schema_editor):
    """Reverse: restore the unique index and original FK constraints."""
    table = 'matches_match'

    # Drop the plain FK constraints
    schema_editor.execute(f"ALTER TABLE {table} DROP FOREIGN KEY matches_match_home_team_id_fk")
    schema_editor.execute(f"ALTER TABLE {table} DROP FOREIGN KEY matches_match_away_team_id_fk")

    # Restore unique index
    schema_editor.execute(
        f"ALTER TABLE {table} "
        f"ADD UNIQUE INDEX unique_tournament_fixture "
        f"(tournament_id, home_team_id, away_team_id)"
    )

    # Re-add FK constraints that reference the unique index
    schema_editor.execute(
        f"ALTER TABLE {table} "
        f"ADD CONSTRAINT matches_match_home_team_id_fk "
        f"FOREIGN KEY (home_team_id) REFERENCES clubs_club(id) ON DELETE CASCADE"
    )
    schema_editor.execute(
        f"ALTER TABLE {table} "
        f"ADD CONSTRAINT matches_match_away_team_id_fk "
        f"FOREIGN KEY (away_team_id) REFERENCES clubs_club(id) ON DELETE CASCADE"
    )


class Migration(migrations.Migration):

    dependencies = [
        ('clubs', '0006_populate_active_formation'),
        ('matches', '0002_match_away_score_match_home_score_substitution_goal_and_more'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='match',
            options={'ordering': ['round_number', 'match_date', 'id']},
        ),

        # Remove the unique constraint (handles MariaDB FK-index dependency)
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.RemoveConstraint(
                    model_name='match',
                    name='unique_tournament_fixture',
                ),
            ],
            database_operations=[
                migrations.RunPython(
                    drop_unique_constraint_forwards,
                    drop_unique_constraint_reverse,
                ),
            ],
        ),

        # New fields
        migrations.AddField(
            model_name='match',
            name='next_match',
            field=models.ForeignKey(
                blank=True,
                help_text='The match whose slot the winner of this match fills',
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='feeder_matches',
                to='matches.match',
            ),
        ),
        migrations.AddField(
            model_name='match',
            name='next_match_slot',
            field=models.CharField(
                blank=True,
                choices=[('home', 'Home'), ('away', 'Away')],
                default='',
                help_text="Which side of next_match the winner fills: 'home' or 'away'",
                max_length=4,
            ),
        ),
        migrations.AddField(
            model_name='match',
            name='penalty_away_score',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='match',
            name='penalty_home_score',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='match',
            name='round_number',
            field=models.PositiveIntegerField(
                default=1,
                help_text='Bracket round (1 = first round, 2 = next, etc.)',
            ),
        ),

        # Nullable home/away teams
        migrations.AlterField(
            model_name='match',
            name='away_team',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='away_matches',
                to='clubs.club',
            ),
        ),
        migrations.AlterField(
            model_name='match',
            name='home_team',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='home_matches',
                to='clubs.club',
            ),
        ),
    ]
