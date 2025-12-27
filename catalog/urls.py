from django.urls import path
from .views import *

urlpatterns = [
    # Category
    path('categories/', CategoryListView.as_view(), name='category_list'),
    path('categories/create/', CategoryCreateView.as_view(), name='category_create'),
    path('categories/<slug:slug>/edit/', CategoryUpdateView.as_view(), name='category_update'),
    path('categories/<slug:slug>/delete/', CategoryDeleteView.as_view(), name='category_delete'),

    # SubCategory
    path('subcategories/', SubCategoryListView.as_view(), name='subcategory_list'),
    path('subcategories/create/', SubCategoryCreateView.as_view(), name='subcategory_create'),
    path('subcategories/<slug:slug>/edit/', SubCategoryUpdateView.as_view(), name='subcategory_update'),  # Add this
    path('subcategories/<slug:slug>/delete/', SubCategoryDeleteView.as_view(), name='subcategory_delete'),

    # Product
    path('products/', ProductListView.as_view(), name='product_list'),
    path('products/create/', ProductCreateView.as_view(), name='product_create'),
    path('products/<slug:slug>/delete/', ProductDeleteView.as_view(), name='product_delete'),

    # Variants
    path('products/<slug:product_slug>/variants/create/', VariantCreateView.as_view(), name='variant_create'),
    path('variants/<slug:slug>/delete/', VariantDeleteView.as_view(), name='variant_delete'),
    
    # Admin approval URLs
    path('categories/pending/', AdminCategoryApprovalListView.as_view(), name='admin_category_approval_list'),
    path('categories/<slug:slug>/approve/', AdminCategoryApproveView.as_view(), name='admin_category_approve'),  # Fixed typo: 'ategories' to 'categories'
    path('subcategories/pending/', AdminSubCategoryApprovalListView.as_view(), name='admin_subcategory_approval_list'),
    path('subcategories/<slug:slug>/approve/', AdminSubCategoryApproveView.as_view(), name='admin_subcategory_approve'),
]