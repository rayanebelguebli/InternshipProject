# api/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TakeTaskViewSet, TeamViewSet, TaskViewSet, MyTasksViewSet, UserViewSet
from rest_framework.authtoken.views import obtain_auth_token

router = DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'teams', TeamViewSet)
router.register(r'tasks', TaskViewSet)
router.register(r'mytasks', MyTasksViewSet)
router.register(r'take_task', TakeTaskViewSet, basename='take_task')


urlpatterns = [
    path('', include(router.urls)),
    path('api-token-auth/', obtain_auth_token, name='api_token_auth'),
]
