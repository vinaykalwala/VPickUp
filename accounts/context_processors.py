# your_app/context_processors.py
def base_template_context(request):
    """
    Adds base_template variable to all templates based on user role
    """
    if not request.user.is_authenticated:
        base_template = 'base.html'
    elif request.user.role == 'customer':
        base_template = 'base.html'
    else:
        base_template = 'admin_base.html'
    
    return {
        'base_template': base_template,
        'is_customer': request.user.is_authenticated and request.user.role == 'customer',
        'is_store_owner': request.user.is_authenticated and request.user.role == 'store_owner',
        'is_admin_user': request.user.is_authenticated and request.user.role == 'admin',
    }
# 'accounts.context_processors.base_template_context',