from rest_framework.routers import SimpleRouter
from breeds.viewsets import BreedViewSet

router = SimpleRouter()
router.register(r'breeds', BreedViewSet, basename='breeds')

urlpatterns = router.urls