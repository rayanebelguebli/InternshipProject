# api/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TeamViewSet, TaskViewSet, MyTasksViewSet
from rest_framework.authtoken.views import obtain_auth_token

router = DefaultRouter()
router.register(r'teams', TeamViewSet)
router.register(r'tasks', TaskViewSet)
router.register(r'mytasks', MyTasksViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('api-token-auth/', obtain_auth_token, name='api_token_auth'),
]
