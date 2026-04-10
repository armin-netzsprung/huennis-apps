from django.contrib import admin
from mptt.admin import DraggableMPTTAdmin
from .models import WikiNode, CommandLevel

class CommandInline(admin.TabularInline):
    model = CommandLevel
    extra = 1 # Zeigt standardmäßig ein leeres Feld für neue Befehle an

@admin.register(WikiNode)
class WikiAdmin(DraggableMPTTAdmin):
    mptt_level_indent = 20
    # 'display_number' kommt neu dazu:
    list_display = ('tree_actions', 'indented_title', 'display_number', 'order')
    list_display_links = ('indented_title',)
    list_editable = ('order',) # Erlaubt schnelles Sortieren in der Liste
    
    prepopulated_fields = {'slug': ('title',)}
    inlines = [CommandInline]

    # Die Funktion für die Spalte im Admin
    def display_number(self, obj):
        return obj.get_number()
    display_number.short_description = "Nr."

    fieldsets = (
        (None, {'fields': ('title', 'slug', 'parent', 'order')}),
        ('Inhalt', {'fields': ('content',)}),
    )

    