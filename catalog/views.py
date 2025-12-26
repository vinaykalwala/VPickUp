from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import SessionAuthentication
from django.shortcuts import render, redirect, get_object_or_404
from .models import *
from . serializers import *
from .forms import *
class CategoryListView(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role == 'admin' or request.user.is_superuser:
            qs = Category.objects.all()
        else:
            store = request.user.stores.first()
            qs = Category.objects.filter(
                models.Q(is_global=True) | models.Q(store=store),
                is_active=True
            )
        return render(request, 'catalog/category_list.html', {'categories': qs})

class CategoryCreateView(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return render(request, 'catalog/category_form.html', {'form': CategoryForm()})

    def post(self, request):
        form = CategoryForm(request.POST)
        serializer = CategorySerializer(data=request.POST)

        if not serializer.is_valid():
            return render(request, 'catalog/category_form.html', {
                'form': form,
                'error': serializer.errors
            })

        category = serializer.save(created_by=request.user)

        if request.user.role == 'store_owner':
            category.store = request.user.stores.first()
            category.is_global = False
            category.is_approved = False
        else:
            category.is_global = True
            category.is_approved = True

        category.save()
        return redirect('category_list')

class CategoryUpdateView(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, slug):
        obj = get_object_or_404(Category, slug=slug)
        return render(request, 'catalog/category_form.html', {
            'form': CategoryForm(instance=obj), 'edit': True
        })

    def post(self, request, slug):
        obj = get_object_or_404(Category, slug=slug)
        serializer = CategorySerializer(obj, data=request.POST)
        form = CategoryForm(request.POST, instance=obj)

        if not serializer.is_valid():
            return render(request, 'catalog/category_form.html', {
                'form': form, 'edit': True, 'error': serializer.errors
            })

        serializer.save()
        return redirect('category_list')


class CategoryDeleteView(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, slug):
        get_object_or_404(Category, slug=slug).delete()
        return redirect('category_list')

class SubCategoryListView(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role == 'admin' or request.user.is_superuser:
            qs = SubCategory.objects.all()
        else:
            store = request.user.stores.first()
            qs = SubCategory.objects.filter(
                models.Q(is_global=True) | models.Q(store=store),
                is_active=True
            )
        return render(request, 'catalog/subcategory_list.html', {'subcategories': qs})

class SubCategoryCreateView(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return render(request, 'catalog/subcategory_form.html', {'form': SubCategoryForm()})

    def post(self, request):
        form = SubCategoryForm(request.POST)
        serializer = SubCategorySerializer(data=request.POST)

        if not serializer.is_valid():
            return render(request, 'catalog/subcategory_form.html', {
                'form': form, 'error': serializer.errors
            })

        subcat = serializer.save(created_by=request.user)

        if request.user.role == 'store_owner':
            subcat.store = request.user.stores.first()
        else:
            subcat.is_global = True
            subcat.is_approved = True

        subcat.save()
        return redirect('subcategory_list')

class SubCategoryDeleteView(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, slug):
        get_object_or_404(SubCategory, slug=slug).delete()
        return redirect('subcategory_list')

class ProductListView(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = Product.objects.filter(store=request.user.stores.first())
        return render(request, 'catalog/product_list.html', {'products': qs})

class ProductCreateView(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return render(request, 'catalog/product_form.html', {
            'form': ProductForm(),
            'variant_form': ProductVariantForm()
        })

    def post(self, request):
        form = ProductForm(request.POST, request.FILES)
        vform = ProductVariantForm(request.POST, request.FILES)

        ps = ProductSerializer(data=request.POST)
        vs = ProductVariantSerializer(data=request.POST)

        if not ps.is_valid() or not vs.is_valid():
            return render(request, 'catalog/product_form.html', {
                'form': form,
                'variant_form': vform,
                'error': {**ps.errors, **vs.errors}
            })

        product = ps.save(
            store=request.user.stores.first(),
            created_by=request.user
        )
        vs.save(product=product)
        return redirect('product_list')

class ProductDeleteView(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, slug):
        get_object_or_404(Product, slug=slug).delete()
        return redirect('product_list')

class VariantCreateView(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, product_slug):
        product = get_object_or_404(Product, slug=product_slug)
        return render(request, 'catalog/variant_form.html', {
            'form': ProductVariantForm(),
            'product': product
        })

    def post(self, request, product_slug):
        product = get_object_or_404(Product, slug=product_slug)
        form = ProductVariantForm(request.POST, request.FILES)
        serializer = ProductVariantSerializer(data=request.POST)

        if not serializer.is_valid():
            return render(request, 'catalog/variant_form.html', {
                'form': form, 'product': product, 'error': serializer.errors
            })

        serializer.save(product=product)
        return redirect('product_list')

class VariantDeleteView(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, slug):
        get_object_or_404(ProductVariant, slug=slug).delete()
        return redirect('product_list')

class AdminCategoryApprovalListView(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not (request.user.role == 'admin' or request.user.is_superuser):
            return redirect('dashboard')

        categories = Category.objects.filter(
            is_approved=False,
            is_active=True
        )

        return render(
            request,
            'catalog/admin_category_approval_list.html',
            {'categories': categories}
        )

class AdminCategoryApproveView(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, slug):
        if not (request.user.role == 'admin' or request.user.is_superuser):
            return redirect('dashboard')

        category = get_object_or_404(Category, slug=slug)
        action = request.POST.get('action')

        if action == 'approve':
            category.is_approved = True
            category.is_global = True
            category.store = None

        elif action == 'reject':
            category.is_active = False

        category.save()
        return redirect('admin_category_approval_list')

class AdminSubCategoryApprovalListView(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not (request.user.role == 'admin' or request.user.is_superuser):
            return redirect('dashboard')

        subcategories = SubCategory.objects.filter(
            is_approved=False,
            is_active=True
        )

        return render(
            request,
            'catalog/admin_subcategory_approval_list.html',
            {'subcategories': subcategories}
        )

class AdminSubCategoryApproveView(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, slug):
        if not (request.user.role == 'admin' or request.user.is_superuser):
            return redirect('dashboard')

        subcat = get_object_or_404(SubCategory, slug=slug)
        action = request.POST.get('action')

        if action == 'approve':
            subcat.is_approved = True
            subcat.is_global = True
            subcat.store = None

        elif action == 'reject':
            subcat.is_active = False

        subcat.save()
        return redirect('admin_subcategory_approval_list')

