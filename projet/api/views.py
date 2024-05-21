from django.shortcuts import render

# api/views.py
from rest_framework import viewsets
from app.models import Teams, Task, MyTasks
from .serializers import TeamSerializer, TaskSerializer, MyTasksSerializer
from rest_framework.permissions import IsAuthenticated

class TeamViewSet(viewsets.ModelViewSet):
    queryset = Teams.objects.all()
    serializer_class = TeamSerializer
    permission_classes = [IsAuthenticated]
    

class TaskViewSet(viewsets.ModelViewSet):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]

class MyTasksViewSet(viewsets.ModelViewSet):
    queryset = MyTasks.objects.all()
    serializer_class = MyTasksSerializer
    permission_classes = [IsAuthenticated]

