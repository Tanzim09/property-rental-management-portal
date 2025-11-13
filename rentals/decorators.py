
from django.core.exceptions import PermissionDenied

def role_required(*roles):
    def decorator(view_func):
        def _wrapped(request, *args, **kwargs):
            if not request.user.is_authenticated:
                from django.contrib.auth.views import redirect_to_login
                return redirect_to_login(request.get_full_path())
            profile = getattr(request.user, "profile", None)
            if profile and profile.role in roles:
                return view_func(request, *args, **kwargs)
            if request.user.is_staff and "ADMIN" in roles:
                return view_func(request, *args, **kwargs)
            raise PermissionDenied
        return _wrapped
    return decorator
