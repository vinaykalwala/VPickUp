from django.urls import path
from .views import *

urlpatterns = [
    path('', InventoryListView.as_view(), name='inventory_list'),
    path('create/', InventoryCreateView.as_view(), name='inventory_create'),
    path('<int:pk>/edit/', InventoryUpdateView.as_view(), name='inventory_update'),
    path('<int:pk>/delete/', InventoryDeleteView.as_view(), name='inventory_delete'),
    path('smart-create/',SmartInventoryCreateView.as_view(),name='smart_inventory_create'),
    path('bulk-upload/complete/', BulkInventoryUploadView.as_view(), name='bulk_inventory_upload_complete'),
    path('bulk-upload/results/', BulkUploadResultsView.as_view(), name='bulk_upload_results'),
    path('bulk-upload/template/complete/', DownloadCompleteTemplateView.as_view(), name='download_complete_template'),
]
