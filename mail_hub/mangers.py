from django.db import models
from django.db.models import Q

class EmailQuerySet(models.QuerySet):
    def for_user(self, user):
        return self.filter(account__user=user)

    def in_virtual_folder(self, folder_type, folder_name=None):
        """
        Logik für virtuelle Ordner
        """
        if folder_type == 'unified_inbox':
            # Sucht in allen Konten nach dem Posteingang
            return self.filter(Q(folder_name__iexact="INBOX") | Q(folder_name__iexact="Posteingang"))
        
        if folder_type == 'favorites':
            # Hier könnten wir nach markierten Favoriten filtern
            return self.filter(is_favorite=True) # Falls wir ein Flag 'is_favorite' haben
            
        if folder_type == 'regular' and folder_name:
            return self.filter(folder_name=folder_name)
            
        return self