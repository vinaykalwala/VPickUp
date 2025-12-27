from django.urls import path
from .views import *

urlpatterns = [
    path('', InventoryListView.as_view(), name='inventory_list'),
    path('create/', InventoryCreateView.as_view(), name='inventory_create'),
    path('<int:pk>/edit/', InventoryUpdateView.as_view(), name='inventory_update'),
    path('<int:pk>/delete/', InventoryDeleteView.as_view(), name='inventory_delete'),
    path('smart-create/',SmartInventoryCreateView.as_view(),name='smart_inventory_create'),
]
