from rest_framework.permissions import BasePermission, SAFE_METHODS
import logging

logger = logging.getLogger(__name__)

class UserPermission(BasePermission):
    def has_object_permission(self, request, view, obj):
        logger.debug(f"Object permission check for user: {request.user}")
       
        if request.user.is_anonymous:
            return request.method in SAFE_METHODS

        # Accept "kennel-dogs" as basename, or use 'dogviewset' class name
        if view.basename in ["kennel-dogs", "dog", "all-dogs"]:
            return bool(request.user and request.user.is_authenticated)
        
        return False

    def has_permission(self, request, view):
        logger.debug(f"Permission check for user: {request.user}")
       
        if view.basename in ["kennel-dogs", "dog", "all-dogs"]:
            if request.user.is_anonymous:
                return request.method in SAFE_METHODS

            return bool(request.user and request.user.is_authenticated)

        return False
