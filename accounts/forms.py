# forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import CustomUser

# forms.py
from django import forms
from .models import CustomUser

class CustomUserCreationForm(forms.ModelForm):
    password = forms.CharField(
        label='Passwort', 
        widget=forms.PasswordInput,
        help_text="Geben Sie ein sicheres Passwort ein."
    )

    class Meta:
        model = CustomUser
        fields = ('email', 'first_name', 'last_name', 'password')
        

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ('first_name', 'last_name', 'birth_date', 'phone', 'mobile', 'avatar')
        widgets = {
            'birth_date': forms.DateInput(attrs={'type': 'date'}),
        }
