# api/serializers.py
from rest_framework import serializers
from app.models import Teams, Task, MyTasks
from django.contrib.auth.models import User

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email']

class TeamSerializer(serializers.ModelSerializer):
    manager = UserSerializer(read_only=True)
    members = UserSerializer(many=True, read_only=True)

    class Meta:
        model = Teams
        fields = ['id', 'name', 'manager', 'members']

class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = '__all__'

class MyTasksSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    tasks = TaskSerializer(many=True, read_only=True)

    class Meta:
        model = MyTasks
        fields = ['user', 'tasks']
