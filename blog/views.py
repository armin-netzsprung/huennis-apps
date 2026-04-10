from django.shortcuts import render, get_object_or_404
from .models import BlogPost, Category
# WICHTIG: get_user_model verwenden statt direktem Import von User
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

# Wir holen uns das aktuell aktive User-Modell (dein CustomUser)
User = get_user_model()

def blog_index(request):
    posts = BlogPost.objects.all().order_by('-created_at')
    
    # Filter-Parameter abrufen
    cat_id = request.GET.get('category')
    author_id = request.GET.get('author')
    time_filter = request.GET.get('time')

    # Filtern nach Kategorie
    if cat_id:
        posts = posts.filter(category_id=cat_id)
    
    # Filtern nach Autor
    if author_id:
        posts = posts.filter(author_id=author_id)

    # Erweiterte Zeitfilter
    now = timezone.now()
    today = now.date()

    if time_filter == 'this_week':
        start_of_week = today - timedelta(days=today.weekday())
        posts = posts.filter(created_at__date__gte=start_of_week)
    
    elif time_filter == 'last_week':
        start_of_this_week = today - timedelta(days=today.weekday())
        start_of_last_week = start_of_this_week - timedelta(days=7)
        posts = posts.filter(created_at__date__gte=start_of_last_week, created_at__date__lt=start_of_this_week)

    elif time_filter == 'this_month':
        posts = posts.filter(created_at__year=now.year, created_at__month=now.month)

    elif time_filter == 'last_month':
        first_day_this_month = today.replace(day=1)
        last_day_last_month = first_day_this_month - timedelta(days=1)
        first_day_last_month = last_day_last_month.replace(day=1)
        posts = posts.filter(created_at__date__gte=first_day_last_month, created_at__date__lte=last_day_last_month)

    elif time_filter == 'this_year':
        posts = posts.filter(created_at__year=now.year)

    elif time_filter == 'last_year':
        posts = posts.filter(created_at__year=now.year - 1)
        
    # Daten für die Filter-Dropdowns sammeln
    context = {
        'posts': posts,
        'categories': Category.objects.all(),
        # Hier wird nun das korrekte User-Modell für die Autorenliste genutzt
        'authors': User.objects.filter(blogpost__isnull=False).distinct(),
        'selected_category': cat_id,
        'selected_author': author_id,
        'selected_time': time_filter,
    }
    
    return render(request, 'blog/index.html', context)

def post_detail(request, pk):
    post = get_object_or_404(BlogPost, pk=pk)
    return render(request, 'blog/post_detail.html', {'post': post})