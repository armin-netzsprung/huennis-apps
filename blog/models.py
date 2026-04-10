from django.db import models
# WICHTIG: Den alten User-Import entfernen!
# from django.contrib.auth.models import User 
from django.conf import settings  # Neu hinzugefügt
from tinymce.models import HTMLField

class Category(models.Model):
    name = models.CharField(max_length=100)
    
    class Meta:
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name

class BlogPost(models.Model):
    # ÄNDERUNG: Nutze settings.AUTH_USER_MODEL statt User
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE,
        verbose_name="Autor"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True)
    
    featured_image = models.ImageField(upload_to='blog_images/', blank=True, null=True, verbose_name="Titelbild")
    
    part_title = models.CharField(max_length=200, verbose_name="Teil (z.B. Teil 2: Die Akutphase)")
    chapter_title = models.CharField(max_length=200, verbose_name="Kapitel (z.B. Kapitel 3: Der Tag X)")
    chapter_subtitle = models.CharField(max_length=200, blank=True, verbose_name="Untertitel")
    
    introduction = HTMLField(verbose_name="Kapitel Einleitung")
    content = HTMLField(verbose_name="Hauptinhalt")

    def __str__(self):
        return f"{self.chapter_title}"

class PostDownload(models.Model):
    post = models.ForeignKey(BlogPost, related_name='downloads', on_delete=models.CASCADE)
    file_label = models.CharField(max_length=100, help_text="z.B. Checkliste Notfallplan")
    file = models.FileField(upload_to='downloads/')

    def __str__(self):
        return self.file_label