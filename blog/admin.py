from django.contrib import admin
from .models import BlogPost, Category, PostDownload

class PostDownloadInline(admin.TabularInline):
    model = PostDownload
    extra = 1 # Zeigt standardmäßig ein leeres Feld für Uploads an

@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    list_display = ('chapter_title', 'category', 'author', 'created_at')
    inlines = [PostDownloadInline] # Downloads direkt im Beitrag bearbeitbar
    fieldsets = (
        ("Metadaten", {'fields': ('author', 'category', 'featured_image')}),
        ("Struktur", {'fields': ('part_title', 'chapter_title', 'chapter_subtitle')}),
        ("Inhalt", {'fields': ('introduction', 'content')}),
    )

admin.site.register(Category)
