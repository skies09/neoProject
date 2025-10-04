from rest_framework_nested import routers
from rest_framework_nested.routers import SimpleRouter, NestedSimpleRouter
from breeds.viewsets import BreedViewSet
from adoption.dog.viewsets.all_dogs_viewset import AllDogsViewSet
from adoption.dog.viewsets.dogs_viewset import DogViewSet
from adoption.kennel.viewsets import KennelViewSet, KennelPasswordChangeViewSet
from adoption.auth.viewsets import (
    RegisterViewSet,
    LoginViewSet,
    RefreshViewSet,
    LogoutViewSet,
    PasswordChangeViewSet,
    FirstTimePasswordResetViewSet,
    GeneralPasswordResetViewSet,
)
from contact.viewsets import ContactViewSet


# Base router
router = routers.SimpleRouter()

# ################### BREEDS ################### #
router.register(r"breeds", BreedViewSet, basename="breeds")

# ################### AUTH ##################### #
router.register(r"auth/register", RegisterViewSet, basename="auth-register")
router.register(r"auth/login", LoginViewSet, basename="auth-login")
router.register(r"auth/refresh", RefreshViewSet, basename="auth-refresh")
router.register(r"auth/logout", LogoutViewSet, basename="auth-logout")
router.register(
    r"auth/change-password", PasswordChangeViewSet, basename="auth-change-password"
)
router.register(
    r"auth/first-time-password-reset",
    FirstTimePasswordResetViewSet,
    basename="auth-first-time-password-reset",
)
router.register(
    r"auth/reset-password",
    GeneralPasswordResetViewSet,
    basename="auth-reset-password",
)

# ################### KENNEL ################### #
router.register(
    r"kennels/change-password",
    KennelPasswordChangeViewSet,
    basename="kennels-change-password",
)
router.register(r"kennels", KennelViewSet, basename="kennels")

# ################### ALL DOGS ################# #
router.register(r"dogs", AllDogsViewSet, basename="all-dogs")  # Global list of all dogs

# ################### CONTACT ################### #
router.register(r"contacts", ContactViewSet, basename="contacts")

# ################### NESTED: KENNEL -> DOGS #### #
kennel_router = NestedSimpleRouter(router, r"kennels", lookup="kennel")
kennel_router.register(
    r"dogs", DogViewSet, basename="kennel-dogs"
)  # Kennels's own dogs

# Final urlpatterns
urlpatterns = router.urls + kennel_router.urls
