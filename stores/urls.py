from django.urls import path
from .views import *

urlpatterns = [
    path('stores/', StoreOwnerStoreListView.as_view(), name='store_list'),
    path('stores/create/', StoreCreateView.as_view(), name='store_create'),
    path('stores/<int:store_id>/', StoreDetailView.as_view(), name='store_detail'),
    path('stores/<int:store_id>/update/', StoreUpdateView.as_view(), name='store_update'),
    path('stores/<int:store_id>/delete/', StoreDeleteView.as_view(), name='store_delete'),
    path('stores/<int:store_id>/verification/', StoreVerificationView.as_view(), name='store_verification'),
    path('stores/verificationlist/',AdminStoreVerificationListView.as_view(),name='admin_store_verification_list'),
    path('stores/<int:store_id>/verify/', AdminStoreVerifyView.as_view(), name='admin_store_verify'),
]
