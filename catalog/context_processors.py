from catalog.models import Category

def header_categories(request):
    categories = Category.objects.filter(
        is_active=True
    ).order_by('name')

    selected_address = None

    if request.user.is_authenticated:
        selected_address = (
            request.user.addresses
            .filter(is_selected=True, is_active=True)
            .first()
        )

    return {
        'header_categories': categories,
        'selected_address': selected_address,
    }
