from django.shortcuts import render, get_object_or_404, redirect
from .models import Ad, Category, UserRecommendation, Message
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
from django.db.models.functions import TruncDate
from datetime import timedelta, date
import csv


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
    recent_messages = Message.objects.filter(receiver=request.user).order_by('-created_at')[:5]
    recent_recommendations = UserRecommendation.objects.filter(to_user=request.user).order_by('-created_at')[:3]

    context = {
        'user_ads': user_ads,
        'favorites': favorites,
        'recent_messages': recent_messages,
        'recent_recommendations': recent_recommendations,
    }
    return render(request, 'dashboard.html', context)

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

    query = request.GET.get('query')
    opinion_type = request.GET.get('type')

    if query:
        recs = recs.filter(comment__icontains=query)
    if opinion_type == 'positive':
        recs = recs.filter(is_positive=True)
    elif opinion_type == 'negative':
        recs = recs.filter(is_positive=False)


    last_week = date.today() - timedelta(days=6)
    daily_stats = (
        UserRecommendation.objects.filter(created_at__date__gte=last_week)
        .annotate(day=TruncDate('created_at'))
        .values('day')
        .annotate(count=Count('id'))
        .order_by('day')
    )

    return render(request, 'admin_recommendations.html', {
        'recommendations': recs,
        'daily_stats': daily_stats,
    })

@staff_member_required
def delete_recommendation(request, rec_id):
    rec = get_object_or_404(UserRecommendation, id=rec_id)
    rec.delete()
    messages.success(request, "Opinia została usunięta.")
    return redirect('admin_recommendations')
@login_required
def report_recommendation(request, rec_id):
    rec = get_object_or_404(UserRecommendation, id=rec_id)
    rec.is_reported = True
    rec.save()
    messages.warning(request, "Zgłoszono opinię do moderatora.")
    return redirect('user_profile', rec.to_user.id)

@staff_member_required
def export_recommendations_csv(request):
    recs = UserRecommendation.objects.select_related('from_user', 'to_user').all()

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="opinie.csv"'

    writer = csv.writer(response)
    writer.writerow(['ID', 'Od', 'Dla', 'Typ', 'Komentarz', 'Data', 'Zgłoszona'])

    for r in recs:
        writer.writerow([
            r.id,
            r.from_user.username,
            r.to_user.username,
            'Polecenie' if r.is_positive else 'Niepolecenie',
            r.comment,
            r.created_at.strftime("%Y-%m-%d %H:%M"),
            'TAK' if r.is_reported else ''
        ])

    return response

@login_required
def chat_view(request, ad_id, user_id):
    ad = get_object_or_404(Ad, id=ad_id)
    contact_user = get_object_or_404(User, id=user_id)


    chat_messages = Message.objects.filter(
        ad=ad,
        sender__in=[request.user, contact_user],
        receiver__in=[request.user, contact_user]
    )

    chat_messages.filter(receiver=request.user, is_read=False).update(is_read=True)

    if request.method == 'POST':
        text = request.POST.get('text')
        image = request.FILES.get('image')

        if text or image:
            Message.objects.create(
                sender=request.user,
                receiver=contact_user,
                ad=ad,
                text=text or "",
                image=image
            )
            return redirect('chat', ad_id=ad.id, user_id=contact_user.id)

    return render(request, 'chat.html', {
        'ad': ad,
        'contact_user': contact_user,
        'chat_messages': chat_messages
    })

@login_required
def inbox_view(request):
    conversations = []

    messages = Message.objects.filter(sender=request.user) | Message.objects.filter(receiver=request.user)
    messages = messages.select_related('ad', 'sender', 'receiver')

    convo_map = {}

    for msg in messages.order_by('-created_at'):
        contact = msg.receiver if msg.sender == request.user else msg.sender
        key = (msg.ad.id, contact.id)

        if key not in convo_map:
            convo_map[key] = {
                'ad': msg.ad,
                'contact': contact,
                'last_message': msg,
                'has_unread': msg.receiver == request.user and not msg.is_read,
            }

    conversations = list(convo_map.values())

    return render(request, 'inbox.html', {'conversations': conversations})