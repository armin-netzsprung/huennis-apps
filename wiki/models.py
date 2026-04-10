from django.db import models
from django.utils.text import slugify
from mptt.models import MPTTModel, TreeForeignKey
from tinymce.models import HTMLField

class WikiNode(MPTTModel):
    title = models.CharField(max_length=255, verbose_name="Titel")
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    
    # Die Baumstruktur-Verknüpfung
    parent = TreeForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children',
        verbose_name="Übergeordnetes Kapitel"
    )
    
    # Der Hauptinhalt via TinyMCE
    content = HTMLField(verbose_name="Inhalt / Erklärung", blank=True)
    
    # Manuelle Sortierung innerhalb einer Ebene
    order = models.PositiveIntegerField(default=0, verbose_name="Sortierung")

    class MPTTMeta:
        # Sorgt dafür, dass MPTT die Baumstruktur anhand deines 'order'-Feldes aufbaut
        order_insertion_by = ['order']

    class Meta:
        verbose_name = "Wiki-Eintrag"
        verbose_name_plural = "Wiki-Einträge"

    def get_number(self):
        """
        Berechnet die hierarchische Nummerierung (z.B. 1.2.1) live basierend 
        auf der Position im Baum und dem 'order'-Feld.
        """
        ancestors = self.get_ancestors(include_self=True)
        num_list = []
        for ancestor in ancestors:
            # Zähle alle Geschwister auf derselben Ebene, die eine kleinere 'order' haben
            pos = WikiNode.objects.filter(
                parent=ancestor.parent, 
                order__lt=ancestor.order
            ).count() + 1
            num_list.append(str(pos))
        return ".".join(num_list)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        # Zeigt im Admin direkt die Nummer vor dem Titel an (sehr hilfreich!)
        return f"{self.get_number()} {self.title}"

class CommandLevel(models.Model):
    """ Die extra Ebene für Befehle wie sudo """
    node = models.ForeignKey(WikiNode, related_name='commands', on_delete=models.CASCADE)
    command = models.TextField(verbose_name="Terminal Befehl")
    description = models.CharField(max_length=255, blank=True, verbose_name="Beschreibung")
    is_sudo = models.BooleanField(default=False, verbose_name="Sudo erforderlich")

    class Meta:
        verbose_name = "Befehl"
        verbose_name_plural = "Befehle"

    def __str__(self):
        prefix = "sudo " if self.is_sudo else ""
        return f"{prefix}{self.command[:30]}"
