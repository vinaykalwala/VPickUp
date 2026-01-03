from django.contrib import admin
from django.urls import path , include
from django.conf import settings
from django.conf.urls.static import static
import Pickup.views as views
from Pickup.views import *
urlpatterns = [
    path("admin/", admin.site.urls),
    path('', views.home, name='home'),
    path('', include('accounts.urls')),
    path('', include('stores.urls')),
    path('catalog/', include('catalog.urls')),
    path('inventory/', include('inventory.urls')),

    path("terms/", views.terms, name="terms"),
    path("privacy/", views.privacy, name="privacy"),
    path("faq/", views.faq, name="faq"),

    path('sliders/', SliderListView.as_view(), name='slider_list'),
    path('sliders/add/', SliderCreateView.as_view(), name='slider_create'),
    path('sliders/<int:pk>/edit/', SliderUpdateView.as_view(), name='slider_update'),
    path('sliders/<int:pk>/delete/', SliderDeleteView.as_view(), name='slider_delete'),

    path('banners/', BannerListView.as_view(), name='banner_list'),
    path('banners/add/', BannerCreateView.as_view(), name='banner_create'),
    path('banners/<int:pk>/edit/', BannerUpdateView.as_view(), name='banner_update'),
    path('banners/<int:pk>/delete/', BannerDeleteView.as_view(), name='banner_delete'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
