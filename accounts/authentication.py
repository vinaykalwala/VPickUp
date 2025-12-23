from django.contrib.auth.backends import ModelBackend
from django.db.models import Q
from .models import User


class UsernameEmailPhoneBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            user = User.objects.get(
                Q(username=username) |
                Q(email=username) |
                Q(phone_number=username)
            )
        except User.DoesNotExist:
            return None

        return user if user.check_password(password) else None
