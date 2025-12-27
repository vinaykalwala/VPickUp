from django.contrib import admin
from django.urls import path , include
from django.conf import settings
from django.conf.urls.static import static
import Pickup.views as views

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
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
