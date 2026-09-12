from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class Comment(models.Model):
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='comments',
    )
    tournament = models.ForeignKey(
        'organizer.Tournament',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='comments',
    )
    match = models.ForeignKey(
        'matches.Match',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='comments',
    )
    text = models.TextField(max_length=1000)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def clean(self):
        super().clean()
        if bool(self.tournament_id) == bool(self.match_id):
            raise ValidationError(
                "A comment must be attached to exactly one of tournament or match, not both or neither."
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        target = self.tournament or self.match
        return f"Comment by {self.author.username} on {target}"
