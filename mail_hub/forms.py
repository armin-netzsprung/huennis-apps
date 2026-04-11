from django import forms
from .models import MailAccount
from .services.crypto import encrypt_string

class MailAccountForm(forms.ModelForm):
    imap_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-input', 'placeholder': 'Passwort'}),
        required=False,
        label="Passwort"
    )

    class Meta:
        model = MailAccount
        # smtp_host und smtp_port HIER hinzufügen:
        fields = ['email_address', 'display_name', 'auth_type', 'imap_host', 'smtp_host', 'smtp_port', 'is_priority']
        widgets = {
            'email_address': forms.EmailInput(attrs={'class': 'form-input'}),
            'display_name': forms.TextInput(attrs={'class': 'form-input'}),
            'auth_type': forms.Select(attrs={'class': 'form-select'}),
            'imap_host': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'imap.ionos.de'}),
            'smtp_host': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'smtp.ionos.de'}),
            'smtp_port': forms.NumberInput(attrs={'class': 'form-input'}),
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
    