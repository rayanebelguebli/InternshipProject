
from datetime import datetime
from django.shortcuts import render

# api/views.py
from rest_framework import viewsets,filters
from app.models import Teams, Task, MyTasks
from .serializers import StageSerializer, TeamSerializer, TaskSerializer, MyTasksSerializer, UserSerializer
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth.models import User
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.response import Response
import xmlrpc.client
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework import status



class TeamViewSet(viewsets.ModelViewSet):
    queryset = Teams.objects.all()
    serializer_class = TeamSerializer
    permission_classes = [IsAuthenticated]
    

class TaskViewSet(viewsets.ModelViewSet):
    
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['maintenance_team_id']
    
    def list(self, request, *args, **kwargs):
        sync_with_odoo()
        return super().list(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        sync_with_odoo()
        return super().retrieve(request, *args, **kwargs)


class MyTasksViewSet(viewsets.ModelViewSet):
    queryset = MyTasks.objects.all()
    serializer_class = MyTasksSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'], url_path='search-by-username')
    def search_by_username(self, request):
        username = request.query_params.get('username', '')
        if username:
            user = User.objects.filter(username=username).first()
            if user:
                sync_with_odoo()
                my_tasks = MyTasks.objects.filter(user=user)
                serializer = self.get_serializer(my_tasks, many=True)
                return Response(serializer.data)
            else:
                return Response({'message': 'Utilisateur non trouvé'}, status=404)
        else:
            return Response({'message': 'Veuillez fournir un nom d\'utilisateur valide'}, status=400)



class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['username', 'first_name', 'last_name', 'email']

    @action(detail=False, methods=['get'], url_path='search-technicians-teams')
    def search_technicians_teams(self, request):
        search_term = request.query_params.get('search', '')
        if search_term:
            technicians = User.objects.filter(
                username__icontains=search_term
            ) | User.objects.filter(
                first_name__icontains=search_term
            ) | User.objects.filter(
                last_name__icontains=search_term
            ) | User.objects.filter(
                email__icontains=search_term
            )
        else:
            technicians = User.objects.none()

        technicians_teams = {technician.id: technician.teams_set.first().id if technician.teams_set.first() else None for technician in technicians}
        return Response(technicians_teams)
    
class TakeTaskViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]

    def create(self, request):
        user_id = request.data.get('userId')
        task_id = request.data.get('taskId')

        try:
            user = User.objects.get(id=user_id)
            task = Task.objects.get(id=task_id)
            now = datetime.now()
            formatted_now = now.strftime('%Y-%m-%d %H:%M:%S')

            url = 'https://rcm.esac.pt/'
            db = 'odoo'
            username = 'admin'
            password = 'admin'
          
            common = xmlrpc.client.ServerProxy('{}/xmlrpc/2/common'.format(url))
            uid = common.authenticate(db, username, password, {})
            models = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(url))

            result = models.execute_kw(
                db, uid, password,
                'maintenance.request', 'write',
                [[int(task_id)], {'stage_id': 2, 'user_id': int(user_id), 'schedule_date': formatted_now}]
            )

            if result:
                my_tasks, _ = MyTasks.objects.get_or_create(user=user)
                my_tasks.tasks.add(task)
                my_tasks.save()
                task.user_id = user.id
                task.save()


                return Response({"message": "La tâche a été mise à jour avec succès."}, status=status.HTTP_200_OK)
            else:
                return Response({"message": "La tâche n'a pas pu être mise à jour."}, status=status.HTTP_400_BAD_REQUEST)

        except User.DoesNotExist:
            return Response({"message": "L'utilisateur n'existe pas."}, status=status.HTTP_404_NOT_FOUND)
        except Task.DoesNotExist:
            return Response({"message": "La tâche n'existe pas."}, status=status.HTTP_404_NOT_FOUND)
        

class UpdateTaskViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def create(self, request):
        task_id = request.data.get('taskId')
        user_id = request.data.get('userId')
        stage_id = request.data.get('stageId')
        sync_with_odoo()

        try:
            user = User.objects.get(id=user_id)
            task = Task.objects.get(id=task_id)

            url = 'https://rcm.esac.pt/'
            db = 'odoo'
            username = 'admin'
            password = 'admin'

            common = xmlrpc.client.ServerProxy('{}/xmlrpc/2/common'.format(url))
            uid = common.authenticate(db, username, password, {})
            models = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(url))

            result = models.execute_kw(
                db, uid, password,
                'maintenance.request', 'write',
                [[int(task_id)], {'stage_id': int(stage_id)}]
            )

            if result:
                return Response({"message": "La tâche a été mise à jour avec succès."}, status=status.HTTP_200_OK)
            else:
                return Response({"message": "La tâche n'a pas pu être mise à jour."}, status=status.HTTP_400_BAD_REQUEST)

        except (User.DoesNotExist, Task.DoesNotExist):
            return Response({"message": "L'utilisateur ou la tâche n'existe pas."}, status=status.HTTP_404_NOT_FOUND)


def sync_with_odoo():

    url = 'https://rcm.esac.pt/'
    db = 'odoo'
    username = 'admin'
    password = 'admin'
    common = xmlrpc.client.ServerProxy('{}/xmlrpc/2/common'.format(url))
    uid = common.authenticate(db, username, password, {})
    models = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(url))
    # Récupérer les tâches depuis Odoo
    tasks = models.execute_kw(
        db, uid, password,
        'maintenance.request',
        'search_read',
        [[]],
        {'fields': ['id', 'name', 'stage_id', 'maintenance_type', 'user_id', 'priority', 'schedule_date', 'equipment_id', 'description', 'maintenance_team_id', 'create_date']}
    )

    odoo_task_ids = []
    for task_data in tasks:
        task_id = task_data['id']
        odoo_task_ids.append(task_id)
        existing_task = Task.objects.filter(id=task_id).first()
        if existing_task:
            existing_task.name = task_data['name']
            existing_task.stage_id = task_data['stage_id'][0]
            existing_task.maintenance_type = task_data['maintenance_type']
            if 'user_id' in task_data and isinstance(task_data['user_id'], list) and task_data['user_id']:
                existing_task.user_id = task_data['user_id'][0]
            else:
                existing_task.user_id = None
            existing_task.priority = task_data['priority']
            existing_task.equipment_id = task_data['equipment_id'][0]
            existing_task.description = task_data['description']
            existing_task.maintenance_team_id = task_data.get('maintenance_team_id', False) and task_data['maintenance_team_id'][0]
            existing_task.create_date = task_data['create_date']
            existing_task.schedule_date = task_data['schedule_date']
            existing_task.save()
        else:
            user_id = None
            if 'user_id' in task_data and isinstance(task_data['user_id'], list) and task_data['user_id']:
                user_id = task_data['user_id'][0]
            else:
                user_id = None
            task = Task(
                id=task_id,
                name=task_data['name'],
                stage_id=task_data['stage_id'][0],
                maintenance_type=task_data['maintenance_type'],
                user_id=user_id,
                priority=task_data['priority'],
                equipment_id=task_data['equipment_id'][0],
                description=task_data['description'],
                maintenance_team_id=task_data.get('maintenance_team_id', False) and task_data['maintenance_team_id'][0],
                create_date=task_data['create_date'],
                schedule_date=task_data['schedule_date']
            )
            task.save()

    Task.objects.exclude(id__in=odoo_task_ids).delete()

class StageViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def list(self, request):
        url = 'https://rcm.esac.pt/'
        db = 'odoo'
        username = 'admin'
        password = 'admin'

        common = xmlrpc.client.ServerProxy('{}/xmlrpc/2/common'.format(url))
        uid = common.authenticate(db, username, password, {})
        models = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(url))

        stages = models.execute_kw(
            db, uid, password, 'maintenance.stage', 'search_read',
            [[]],
            {'fields': ['id', 'name', 'done']}
        )

        return Response(stages)
