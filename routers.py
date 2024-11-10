# routers.py (or wherever your routers are defined)

from rest_framework_nested import routers
from breeds.viewsets import BreedViewSet
from adoption.dog.viewsets import DogViewSet
from adoption.kennel.viewsets import KennelViewSet
from adoption.auth.viewsets import (
    RegisterViewSet,
    LoginViewSet,
    RefreshViewSet,
    LogoutViewSet,
    PasswordChangeViewSet
)

router = routers.SimpleRouter()


# ##################################################################### #
# ################### BREEDS                     ###################### #
# ##################################################################### #

router.register(r'breeds', BreedViewSet, basename='breeds')

# ##################################################################### #
# ################### AUTH                       ###################### #
# ##################################################################### #

router.register(r"auth/register", RegisterViewSet, basename="auth-register")
router.register(r"auth/login", LoginViewSet, basename="auth-login")
router.register(r"auth/refresh", RefreshViewSet, basename="auth-refresh")
router.register(r"auth/logout", LogoutViewSet, basename="auth-logout")
router.register(r"auth/change-password", PasswordChangeViewSet, basename="auth-change-password")

# ##################################################################### #
# ################### KENNEL                     ###################### #
# ##################################################################### #

router.register(r"kennel", KennelViewSet, basename="kennel")


# ##################################################################### #
# ################### DOG                        ###################### #
# ##################################################################### #

router.register(r"dog", DogViewSet, basename="dog")

dogs_router = routers.NestedSimpleRouter(router, r"dog", lookup="dog")

urlpatterns = [*router.urls, *dogs_router.urls]
