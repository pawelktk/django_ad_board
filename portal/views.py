from django.shortcuts import render, get_object_or_404, redirect
from .models import Ad, Category, UserRecommendation
from .forms import AdForm, ContactForm
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.contrib import messages
from django.core.paginator import Paginator
from django.core.mail import send_mail
from django.db.models import Count, Q
from django.utils import timezone
from django.contrib.admin.views.decorators import staff_member_required


def ad_list(request):
    category_id = request.GET.get('category')
    query = request.GET.get('q')
    ads = Ad.objects.all().order_by('-created_at')
    categories = Category.objects.all()
    sort = request.GET.get('sort')

    if category_id:
        ads = ads.filter(category_id=category_id)

    if query:
        ads = ads.filter(
            Q(title__icontains=query) | Q(description__icontains=query)
        )
    if sort == 'price_asc':
        ads = ads.order_by('price')
    elif sort == 'price_desc':
        ads = ads.order_by('-price')
    else:
        ads = ads.order_by('-created_at')


    paginator = Paginator(ads, 6)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'ad_list.html', {
        'categories': categories,
        'page_obj': page_obj,
        'query': query,
        'sort': sort
    })


def ad_detail(request, ad_id):
    ad = get_object_or_404(Ad, pk=ad_id)
    return render(request, 'ad_detail.html', {'ad': ad})

@login_required
@login_required
def ad_create(request):
    if request.method == 'POST':
        form = AdForm(request.POST, request.FILES)
        if form.is_valid():
            ad = form.save(commit=False)
            ad.user = request.user
            ad.save()
            messages.success(request, "Ogłoszenie zostało dodane!")


            send_mail(
                subject="Dodano nowe ogłoszenie",
                message=f"Twoje ogłoszenie \"{ad.title}\" zostało pomyślnie dodane.",
                from_email=None,
                recipient_list=[request.user.email],
                fail_silently=True,
            )

            return redirect('ad_detail', ad_id=ad.id)
    else:
        form = AdForm()
    return render(request, 'ad_form.html', {'form': form})

@login_required
def ad_edit(request, ad_id):
    ad = get_object_or_404(Ad, pk=ad_id)
    if ad.user != request.user and not request.user.is_staff:
        raise PermissionDenied
    if request.method == 'POST':
        form = AdForm(request.POST,request.FILES, instance=ad)
        if form.is_valid():
            form.save()
            messages.success(request, "Ogłoszenie zostało zaktualizowane!")
            return redirect('ad_detail', ad_id=ad.id)
    else:
        form = AdForm(instance=ad)
    return render(request, 'ad_form.html', {'form': form})

@login_required
def ad_delete(request, ad_id):
    ad = get_object_or_404(Ad, pk=ad_id)
    if ad.user != request.user and not request.user.is_staff:
        raise PermissionDenied
    if request.method == 'POST':
        ad.delete()
        messages.success(request, "Ogłoszenie zostało usunięte.")
        return redirect('ad_list')
    return render(request, 'ad_confirm_delete.html', {'ad': ad})

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('ad_list')
    else:
        form = UserCreationForm()
    return render(request, 'register.html', {'form': form})

def contact(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            return HttpResponse("Dziękujemy za kontakt!")
    else:
        form = ContactForm()
    return render(request, 'contact.html', {'form': form})

def custom_404(request, exception):
    return render(request, 'errors/404.html', status=404)

def custom_500(request):
    return render(request, 'errors/500.html', status=500)


@login_required
def toggle_favorite(request, ad_id):
    ad = get_object_or_404(Ad, id=ad_id)
    if request.user in ad.favorites.all():
        ad.favorites.remove(request.user)
        messages.info(request, "Usunięto z ulubionych.")
    else:
        ad.favorites.add(request.user)
        messages.success(request, "Dodano do ulubionych!")
    return redirect('ad_detail', ad_id=ad_id)

@login_required
def favorites_list(request):
    ads = request.user.favorite_ads.all()
    return render(request, 'favorites_list.html', {'ads': ads})

@login_required
def user_dashboard(request):
    user_ads = Ad.objects.filter(user=request.user).order_by('-created_at')
    favorites = request.user.favorite_ads.all()
    return render(request, 'dashboard.html', {
        'user_ads': user_ads,
        'favorites': favorites,
    })

@staff_member_required
def admin_dashboard(request):
    total_ads = Ad.objects.count()
    active_ads = Ad.objects.filter(expires_at__gt=timezone.now()).count()
    expired_ads = Ad.objects.filter(expires_at__lt=timezone.now()).count()
    users_count = User.objects.count()
    categories_count = Category.objects.count()

    return render(request, 'admin_dashboard.html', {
        'total_ads': total_ads,
        'active_ads': active_ads,
        'expired_ads': expired_ads,
        'users_count': users_count,
        'categories_count': categories_count,
    })

def user_profile(request, user_id):
    user_obj = get_object_or_404(User, id=user_id)
    ads = Ad.objects.filter(user=user_obj)

    recommendations = UserRecommendation.objects.filter(to_user=user_obj)
    can_recommend = request.user.is_authenticated and request.user != user_obj and not recommendations.filter(from_user=request.user).exists()

    stats = {
        'total_ads': ads.count(),
        'active_ads': ads.filter(expires_at__gt=timezone.now()).count(),
        'positive_recommendations': recommendations.filter(is_positive=True).count(),
        'negative_recommendations': recommendations.filter(is_positive=False).count(),
    }

    return render(request, 'user_profile.html', {
        'profile_user': user_obj,
        'ads': ads,
        'recommendations': recommendations,
        'can_recommend': can_recommend,
        'stats': stats,
    })
@login_required
def add_recommendation(request, user_id):
    if request.method == 'POST':
        to_user = get_object_or_404(User, id=user_id)
        if to_user == request.user:
            messages.error(request, "Nie możesz ocenić samego siebie.")
            return redirect('user_profile', user_id=user_id)

        is_positive = request.POST.get('is_positive') == 'true'
        comment = request.POST.get('comment', '')
        try:
            UserRecommendation.objects.create(from_user=request.user, to_user=to_user, is_positive=is_positive, comment=comment)
            messages.success(request, "Opinia dodana!")
        except:
            messages.error(request, "Już dodałeś opinię o tym użytkowniku.")

    return redirect('user_profile', user_id=user_id)

@staff_member_required
def admin_recommendations_panel(request):
    recs = UserRecommendation.objects.select_related('from_user', 'to_user').order_by('-created_at')

    # Filtrowanie
    user_id = request.GET.get('user')
    opinion_type = request.GET.get('type')
    if user_id:
        recs = recs.filter(to_user__id=user_id)
    if opinion_type == 'positive':
        recs = recs.filter(is_positive=True)
    elif opinion_type == 'negative':
        recs = recs.filter(is_positive=False)

    return render(request, 'admin_recommendations.html', {
        'recommendations': recs
    })

@staff_member_required
def delete_recommendation(request, rec_id):
    rec = get_object_or_404(UserRecommendation, id=rec_id)
    rec.delete()
    messages.success(request, "Opinia została usunięta.")
    return redirect('admin_recommendations')
