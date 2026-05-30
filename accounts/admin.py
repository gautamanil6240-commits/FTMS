from django.contrib import admin
from .models import UserProfile


class UserProfileAdmin(admin.ModelAdmin):

    list_display = [
        'user',
        'role',
        'is_verified',
        'phone_number',
    ]

    list_filter = [
        'role',
        'is_verified',
    ]

    search_fields = [
        'user__username',
        'user__email',
    ]

    list_editable = ['is_verified']

    actions = ['verify_users']

    def verify_users(self, request, queryset):
        queryset.update(is_verified=True)
        self.message_user(
            request,
            "Selected users verified successfully!"
        )

    verify_users.short_description = "Verify selected users"


admin.site.register(UserProfile, UserProfileAdmin)

admin.site.site_header = "FTMS Admin Panel"
admin.site.site_title = "FTMS Admin"
admin.site.index_title = "Football Tournament Management System"