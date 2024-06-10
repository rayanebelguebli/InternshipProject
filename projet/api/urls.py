# api/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import StageViewSet, TakeTaskViewSet, TeamViewSet, TaskViewSet, MyTasksViewSet, UpdateTaskViewSet, UserViewSet
from rest_framework.authtoken.views import obtain_auth_token

router = DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'teams', TeamViewSet)
router.register(r'tasks', TaskViewSet)
router.register(r'mytasks', MyTasksViewSet)
router.register(r'take_task', TakeTaskViewSet, basename='take_task')
router.register(r'update_task',UpdateTaskViewSet, basename='update_task')
router.register(r'stages', StageViewSet, basename='stage')


urlpatterns = [
    path('', include(router.urls)),
    path('api-token-auth/', obtain_auth_token, name='api_token_auth'),
]
