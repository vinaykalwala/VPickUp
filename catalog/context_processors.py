from catalog.models import Category


def header_categories(request):
    """
    Simple version - shows all active categories
    """
    categories = Category.objects.filter(
        is_active=True
    ).order_by('name')
    
    return {
        'header_categories': categories,
        'header_store': None  # Or remove this if not needed
    }