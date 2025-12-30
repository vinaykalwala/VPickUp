from django.contrib import admin
from .models import *

admin.site.register(User)
admin.site.register(CustomerProfile)
admin.site.register(StoreOwnerProfile)
admin.site.register(CustomerAddress)
