from django.urls import path
from django.contrib.auth import views as auth_views
from .views import signup_view, profile_view # profile_view erstellen wir gleich
from django.views.decorators.csrf import ensure_csrf_cookie

urlpatterns = [
    # path('login/', auth_views.LoginView.as_view(template_name='accounts/login.html'), name='login'),
    path('accounts/login/', ensure_csrf_cookie(auth_views.LoginView.as_view(template_name='accounts/login.html')), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('signup/', signup_view, name='signup'),
    path('profile/', profile_view, name='profile'),

    # Passwort vergessen - Die 4 Schritte
    path('password_reset/', auth_views.PasswordResetView.as_view(
        template_name='accounts/password_reset.html',
        email_template_name='accounts/password_reset_email.html',
        subject_template_name='accounts/password_reset_subject.txt'
    ), name='password_reset'),
    
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='accounts/password_reset_done.html'
    ), name='password_reset_done'),
    
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='accounts/password_reset_confirm.html'
    ), name='password_reset_confirm'),
    
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(
        template_name='accounts/password_reset_complete.html'
    ), name='password_reset_complete'),
]

