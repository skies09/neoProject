from rest_framework.permissions import BasePermission, SAFE_METHODS

class UserPermission(BasePermission):
    def has_object_permission(self, request, view, obj):
        print(f"Object permission check for user: {request.user}, authenticated: {request}1")
       
        if request.user.is_anonymous:
            return request.method in SAFE_METHODS

        if view.basename in ["dog"]:
            return bool(request.user and request.user.is_authenticated)
        
        return False

    def has_permission(self, request, view):
        print(f"Permission check for user: {request.user}, authenticated: {request}")
       
        if view.basename in ["dog"]:
            if request.user.is_anonymous:
                return request.method in SAFE_METHODS

            return bool(request.user and request.user.is_authenticated)

        return False