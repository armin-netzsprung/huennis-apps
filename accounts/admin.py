from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _
from .models import CustomUser
from .forms import CustomUserCreationForm

@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin): # <--- Geändert von UserAdmin auf ModelAdmin
    add_form = CustomUserCreationForm
    
    ordering = ('email',)
    list_display = ('email', 'first_name', 'last_name', 'is_staff', 'is_active')
    search_fields = ('email', 'first_name', 'last_name')
    list_filter = ('is_staff', 'is_superuser', 'is_active')

    # Feldsets für die Detailansicht
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Persönliche Info'), {'fields': ('first_name', 'last_name', 'birth_date', 'avatar')}),
        (_('Kontakt'), {'fields': ('phone', 'mobile')}),
        (_('Systemdaten'), {'fields': ('seafile_auth_token',)}),
        (_('Berechtigungen'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        (_('Wichtige Daten'), {'fields': ('last_login', 'date_joined')}),
    )

    # Diese Methode sorgt dafür, dass beim Anlegen (Add) das Passwort-Formular kommt
    def get_fieldsets(self, request, obj=None):
        if not obj:
            return (
                (None, {
                    'classes': ('wide',),
                    'fields': ('email', 'first_name', 'last_name', 'password'),
                }),
            )
        return super().get_fieldsets(request, obj)

    def save_model(self, request, obj, form, change):
        # Falls das Passwort im Formular geändert wurde (beim Anlegen oder Bearbeiten)
        if 'password' in form.cleaned_data:
            # Nur setzen, wenn es nicht bereits ein Hash ist (wichtig für Add-View)
            if not form.cleaned_data['password'].startswith(('pbkdf2_sha256$', 'bcrypt$', 'argon2$')):
                obj.set_password(form.cleaned_data['password'])
        super().save_model(request, obj, form, change)
