from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User

class Teams(models.Model):
    id = models.IntegerField(primary_key=True)  # ID ajouté manuellement
    name = models.CharField(max_length=100)
    manager = models.ForeignKey(User, on_delete=models.CASCADE, related_name='managed_teams', null=True, blank=True)
    members = models.ManyToManyField(User)

    def __str__(self):
        return self.name
    
class Task(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=255)
    stage_id = models.CharField(max_length=255)
    maintenance_type = models.CharField(max_length=255)
    user_id = models.IntegerField(null=True)  
    priority = models.CharField(max_length=255)
    equipment_id = models.IntegerField(null=True)
    description = models.TextField()
    instruction_text = models.TextField()
    maintenance_team_id = models.CharField(max_length=255)
    create_date = models.CharField(max_length=255, default=timezone.now)
    schedule_date = models.CharField(max_length=255, default=timezone.now)

def __str__(self):
    return self.name

class MyTasks(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    tasks = models.ManyToManyField('Task', related_name='mytasks')

class Equipment(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    maintenance_team_id = models.IntegerField(null=True)