from django.contrib import admin
from .models import CoachProfile, PlayerPerformance, Formation, LineupSlot

@admin.register(CoachProfile)
class CoachProfileAdmin(admin.ModelAdmin):
    # This will let you see the coach's name and their linked club directly in a clear table layout
    list_display = ('id', 'full_name', 'phone_number')


@admin.register(PlayerPerformance)
class PlayerPerformanceAdmin(admin.ModelAdmin):
    list_display = ('id', 'player', 'coach', 'performance_date', 'match_title', 'goals', 'assists', 'rating')
    list_filter = ('performance_date', 'rating')
    search_fields = ('player__full_name', 'match_title', 'notes')
    date_hierarchy = 'performance_date'


# ==========================================
# TACTICAL LINEUP / FORMATION ADMIN
# ==========================================
class LineupSlotInline(admin.TabularInline):
    model = LineupSlot
    extra = 0
    fields = ('slot_key', 'label', 'top', 'left', 'position_hint', 'player')
    ordering = ('slot_key',)


@admin.register(Formation)
class FormationAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'club', 'updated_at')
    list_filter = ('name',)
    search_fields = ('club__name', 'name')
    inlines = [LineupSlotInline]


@admin.register(LineupSlot)
class LineupSlotAdmin(admin.ModelAdmin):
    list_display = ('id', 'formation', 'slot_key', 'label', 'player', 'position_hint')
    list_filter = ('position_hint',)
    search_fields = ('label', 'slot_key', 'player__full_name', 'formation__club__name')

