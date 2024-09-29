from django.urls import path
from . import views

app_name = 'adoptionDogs'
urlpatterns = [
    # adoption dog views
    path('', views.adoption_list, name='adoption-list'),
    path('dod', views.dog_of_the_day, name='dog-of-the-day'),
    # path('detail', views.adoption_dog_detail, name='adoption-dog-detail'),
]