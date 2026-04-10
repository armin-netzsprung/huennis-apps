# ### NICHT LÖSCHEN ### #
# SITE_IDENTITY=office python manage.py mail_runner --all
# python manage.py mail_runner --account dein-test@gmx.de
# python manage.py mail_runner --user armin
# ### #

# ### NICHT LÖSCHEN ### #
# SITE_IDENTITY=office python manage.py shell

# from mail_hub.models import MailAccount
# from mail_hub.services.crypto import encrypt_string
# from django.contrib.auth import get_user_model

# user = get_user_model().objects.get(username='armin.huenniger@netzsprung.de')
# acc = MailAccount.objects.create(
#     user=user,
#     email_address='armin.huenniger@netzsprung.de',
#     auth_type='imap_pwd',
#     encrypted_credentials=encrypt_string('ArmLeicht48#')
# )
# ###

import logging
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from mail_hub.models import MailAccount
# Wir importieren die Protokolle später dynamisch oder hier direkt
from mail_hub.services.protocols import imap, graph

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Startet den E-Mail-Abruf für konfigurierte Konten.'

    def add_arguments(self, parser):
        parser.add_argument('--all', action='store_true', help='Alle aktiven Accounts synchronisieren')
        parser.add_argument('--user', type=str, help='Nur Accounts eines bestimmten Users (Username)')
        parser.add_argument('--account', type=str, help='Nur eine bestimmte E-Mail-Adresse synchronisieren')

    def handle(self, *args, **options):
        queryset = MailAccount.objects.filter(is_active=True)

        # Flexible Filterung (Anforderung 3)
        if options['account']:
            queryset = queryset.filter(email_address=options['account'])
        elif options['user']:
            queryset = queryset.filter(user__username=options['user'])
        elif not options['all']:
            self.stdout.write(self.style.WARNING("Bitte --all, --user oder --account angeben."))
            return

        self.stdout.write(self.style.SUCCESS(f"Starte Sync für {queryset.count()} Account(s)..."))

        for account in queryset:
            self.stdout.write(f"Verarbeite: {account.email_address} ({account.auth_type})")
            
            try:
                if account.auth_type == 'imap_pwd':
                    imap.sync_account(account)
                elif account.auth_type == 'ms_graph':
                    graph.sync_account(account)
                elif account.auth_type == 'google':
                    self.stdout.write(self.style.NOTICE("Google Auth noch nicht implementiert."))
                
                # Zeitstempel für erfolgreichen Sync setzen
                from django.utils.timezone import now
                account.last_sync_at = now()
                account.save(update_fields=['last_sync_at'])
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Fehler bei {account.email_address}: {str(e)}"))
    