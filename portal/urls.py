from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', views.ad_list, name='ad_list'),
    path('ad/<int:ad_id>/', views.ad_detail, name='ad_detail'),
    path('ad/create/', views.ad_create, name='ad_create'),
    path('ad/<int:ad_id>/edit/', views.ad_edit, name='ad_edit'),
    path('ad/<int:ad_id>/delete/', views.ad_delete, name='ad_delete'),
    path('contact/', views.contact, name='contact'),
    path('register/', views.register, name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='/'), name='logout'),
    path('favorites/', views.favorites_list, name='favorites_list'),
    path('ad/<int:ad_id>/favorite/', views.toggle_favorite, name='toggle_favorite'),
    path('dashboard/', views.user_dashboard, name='user_dashboard'),
    path('admin-panel/', views.admin_dashboard, name='admin_dashboard'),
    path('uzytkownik/<int:user_id>/', views.user_profile, name='user_profile'),
    path('uzytkownik/<int:user_id>/dodaj-opinie/', views.add_recommendation, name='add_recommendation'),
]

from django.conf import settings
from django.conf.urls.static import static

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)