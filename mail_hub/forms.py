from django import forms
from .models import MailAccount
from .services.crypto import encrypt_string

class MailAccountForm(forms.ModelForm):
    # Wir fügen ein virtuelles Feld für das Passwort hinzu, damit wir das 
    # verschlüsselte Feld 'encrypted_credentials' nicht direkt zeigen müssen
    imap_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-input', 'placeholder': 'Passwort'}),
        required=False,
        label="IMAP Passwort",
        help_text="Nur ausfüllen, wenn Sie ein IMAP-Konto nutzen oder das Passwort ändern möchten."
    )

    class Meta:
        model = MailAccount
        fields = ['email_address', 'display_name', 'auth_type', 'imap_host', 'is_priority']
        widgets = {
            'email_address': forms.EmailInput(attrs={'class': 'form-input'}),
            'display_name': forms.CharField.widget(attrs={'class': 'form-input'}),
            'auth_type': forms.Select(attrs={'class': 'form-select'}),
            'imap_host': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g. imap.ionos.de'}),
        }

    def save(self, commit=True):
        instance = super().save(commit=False)
        password = self.cleaned_data.get('imap_password')
        
        # Falls ein Passwort eingegeben wurde, verschlüsseln wir es
        if password:
            instance.encrypted_credentials = encrypt_string(password)
        
        if commit:
            instance.save()
        return instance
    