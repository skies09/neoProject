from django.urls import path
from . import views

app_name = 'breeds'
urlpatterns = [
    # breed views
    path('', views.breeds_list, name='breeds-list'),
    path('groups', views.breed_groups, name='breed-groups'),
    path('groups/<str:group>', views.group_breeds, name='breed-breeds'),
    path('detail', views.breed_detail, name='breed-detail'),
]