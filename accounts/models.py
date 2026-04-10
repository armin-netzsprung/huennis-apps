from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models

class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Die E-Mail-Adresse muss angegeben werden')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        return self.create_user(email, password, **extra_fields)

class CustomUser(AbstractUser):
    username = None
    email = models.EmailField('E-Mail-Adresse', unique=True)
    
    # --- Profil-Informationen ---
    birth_date = models.DateField('Geburtsdatum', null=True, blank=True)
    phone = models.CharField('Telefon', max_length=20, blank=True)
    mobile = models.CharField('Mobil', max_length=20, blank=True)
    avatar = models.ImageField('Profilbild', upload_to='avatars/', null=True, blank=True)
    
    # --- Systemdaten (Seafile etc.) ---
    seafile_auth_token = models.CharField('Seafile Auth Code', max_length=255, blank=True)
    # Später erweiterbar um seafile_user, seafile_library_id etc.

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name'] # Diese werden beim createsuperuser abgefragt

    objects = CustomUserManager()

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.email})"

