from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.contrib.auth.models import User, Group
from .models import Teams, Task, MyTasks, Equipment, UploadedModel
from django.db.models import Q
from datetime import datetime
import xmlrpc.client
from xmlrpc.client import Fault
from .forms import UploadModelForm

url = 'http://192.168.1.244:8069'
db = 'db_test'
username = 'admin'
password = 'admin'

common = xmlrpc.client.ServerProxy('{}/xmlrpc/2/common'.format(url))
uid = common.authenticate(db, username, password, {})
models = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(url))

def is_admin_or_manager_or_technicien(user):
    return user.groups.filter(name__in=['Admin', 'Manager', 'Technicien']).exists()

def is_admin_or_manager(user):
    return user.groups.filter(name__in=['Admin', 'Manager']).exists()

def is_admin(user):
    return user.groups.filter(name='Admin').exists()

def is_technicien(user):
    return user.groups.filter(name='Technicien').exists()

def is_manager(user):
    return user.groups.filter(name='Manager').exists()

def user_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('home')  
        messages.error(request, 'Identifiant ou mot de passe incorrect.')
    return render(request, 'app/login.html')

@user_passes_test(is_admin_or_manager_or_technicien)
@login_required
def home(request):
    sync_equipments_from_odoo()
    sync_with_odoo()
    user = request.user
    user_groups = user.groups.all()
    teams = Teams.objects.filter(members=user)
    managed_teams = Teams.objects.filter(manager=user).values_list('name', flat=True)
    technician_teams = teams.values_list('name', flat=True)
    stages = models.execute_kw(
        db, uid, password, 'maintenance.stage', 'search_read',
        [[]],
        {'fields': ['id', 'name', 'done']}
    )
    user_tasks = Task.objects.filter(user_id=request.user.id)

    can_create_team = False
    if user.groups.filter(id=2).exists() and not Teams.objects.filter(manager=user).exists():
        can_create_team = True

    tasks = Task.objects.filter(
        Q(maintenance_team_id__in=teams) & Q(stage_id=1))

    context = {
        'can_create_team': can_create_team,
        'user': user,
        'user_groups': user_groups,
        'managed_teams': managed_teams,
        'technician_teams': technician_teams,
        'tasks': tasks,
        'user_tasks': user_tasks, 
        'stages': stages
    }
    
    return render(request, 'app/home.html', context)

@login_required
@user_passes_test(is_admin)
def add_manager(request):
    user = request.user
    user_groups = user.groups.all()
    teams = Teams.objects.filter(members=user)
    managed_teams = Teams.objects.filter(manager=user).values_list('name', flat=True)
    technician_teams = teams.values_list('name', flat=True)
    stages = models.execute_kw(
        db, uid, password, 'maintenance.stage', 'search_read',
        [[]],
        {'fields': ['id', 'name', 'done']}
    )
    user_tasks = Task.objects.filter(user_id=request.user.id)

    can_create_team = False
    if user.groups.filter(id=2).exists() and not Teams.objects.filter(manager=user).exists():
        can_create_team = True

    tasks = Task.objects.filter(
        Q(maintenance_team_id__in=teams) & Q(stage_id=1))

    context = {
        'can_create_team': can_create_team,
        'user': user,
        'user_groups': user_groups,
        'managed_teams': managed_teams,
        'technician_teams': technician_teams,
        'tasks': tasks,
        'user_tasks': user_tasks, 
        'stages': stages
    }

    if request.method == 'POST':
        signup_username = request.POST.get('username')
        signup_email = request.POST.get('email')
        signup_password = request.POST.get('password')
        group_name = 'Manager' 
        
        if not User.objects.filter(username=signup_username).exists():
            group_ids_manager = [17, 24, 32]
            new_user_data = {
                'name': signup_username,  
                'login': signup_email,
                'email' : signup_email,
                'password': signup_password,
                'groups_id': [(6, 0, group_ids_manager)]
            }
            try:
                new_user_id = models.execute_kw(db, uid, password, 'res.users', 'create', [new_user_data])
            
                if new_user_id:
                    user_id = new_user_id
                    user = User.objects.create_user(id=user_id, username=signup_username, email=signup_email, password=signup_password)
                    messages.success(request, 'Utilisateur ajouté avec succès.')
                    group = Group.objects.get(name=group_name)
                    user.groups.add(group)
                else:
                    messages.error(request, 'Erreur lors de la création de l\'utilisateur.')
            except Fault as e:
                messages.error(request, f"Erreur lors de la création de l'utilisateur dans Odoo : {e}")
        else:
            messages.error(request, 'Cet utilisateur existe déjà.')

        return redirect('home')  

    return render(request, 'app/add_manager.html', context)

@login_required
@user_passes_test(is_admin)
def manager_members(request):
    user = request.user
    user_groups = user.groups.all()
    teams = Teams.objects.filter(members=user)
    managed_teams = Teams.objects.filter(manager=user).values_list('name', flat=True)
    technician_teams = teams.values_list('name', flat=True)
    stages = models.execute_kw(
        db, uid, password, 'maintenance.stage', 'search_read',
        [[]],
        {'fields': ['id', 'name', 'done']}
    )
    user_tasks = Task.objects.filter(user_id=request.user.id)

    can_create_team = False
    if user.groups.filter(id=2).exists() and not Teams.objects.filter(manager=user).exists():
        can_create_team = True

    tasks = Task.objects.filter(
        Q(maintenance_team_id__in=teams) & Q(stage_id=1))

    manager_group = Group.objects.get(name='Manager')
    members = manager_group.user_set.all()

    context = {
        'can_create_team': can_create_team,
        'user': user,
        'user_groups': user_groups,
        'managed_teams': managed_teams,
        'technician_teams': technician_teams,
        'tasks': tasks,
        'user_tasks': user_tasks,
        'stages': stages,
        'members': members
    }

    return render(request, 'app/manager_members.html', context)


@login_required
@user_passes_test(is_manager)
@login_required
@user_passes_test(is_manager)
def add_technician(request):
    user = request.user
    user_groups = user.groups.all()
    teams = Teams.objects.filter(members=user)
    managed_teams = Teams.objects.filter(manager=user).values_list('name', flat=True)
    technician_teams = teams.values_list('name', flat=True)
    stages = models.execute_kw(
        db, uid, password, 'maintenance.stage', 'search_read',
        [[]],
        {'fields': ['id', 'name', 'done']}
    )
    user_tasks = Task.objects.filter(user_id=request.user.id)

    can_create_team = False
    if user.groups.filter(id=2).exists() and not Teams.objects.filter(manager=user).exists():
        can_create_team = True

    tasks = Task.objects.filter(
        Q(maintenance_team_id__in=teams) & Q(stage_id=1))

    if request.method == 'POST':
        signup_username = request.POST.get('username')
        signup_email = request.POST.get('email')
        signup_password = request.POST.get('password')
        group_name = 'Technicien'

        if not User.objects.filter(username=signup_username).exists():
            group_ids_technician = [1, 31]
            new_user_data = {
                'name': signup_username,
                'login': signup_email,
                'email': signup_email,
                'password': signup_password,
                'groups_id': [(6, 0, group_ids_technician)]
            }
            try:
                new_user_id = models.execute_kw(db, uid, password, 'res.users', 'create', [new_user_data])

                if new_user_id:
                    user_id = new_user_id
                    user = User.objects.create_user(id=user_id, username=signup_username, email=signup_email,
                                                     password=signup_password)
                    messages.success(request, 'Utilisateur ajouté avec succès.')
                    group = Group.objects.get(name=group_name)
                    user.groups.add(group)

                    manager = request.user
                    manager_team = Teams.objects.filter(manager=manager).first()
                    if manager_team:
                        manager_team.members.add(user)
                        models.execute_kw(
                            db, uid, password, 'maintenance.team', 'write',
                            [[manager_team.id], {'member_ids': [(4, user_id)]}]
                        )
                        messages.success(request, 'Utilisateur ajouté à votre équipe avec succès.')
                    else:
                        messages.error(request, 'Impossible de trouver votre équipe.')

                else:
                    messages.error(request, 'Erreur lors de la création de l\'utilisateur.')
            except Exception as e:
                messages.error(request, f"Erreur lors de la création de l'utilisateur dans Odoo : {e}")
        else:
            messages.error(request, 'Cet utilisateur existe déjà.')

        return redirect('home')

    context = {
        'can_create_team': can_create_team,
        'user': user,
        'user_groups': user_groups,
        'managed_teams': managed_teams,
        'technician_teams': technician_teams,
        'tasks': tasks,
        'user_tasks': user_tasks,
        'stages': stages,
    }

    return render(request, 'app/add_technician.html', context)



@login_required
@user_passes_test(is_manager)
def technician_members(request):
    user = request.user
    user_groups = user.groups.all()
    teams = Teams.objects.filter(members=user)
    managed_teams = Teams.objects.filter(manager=user).values_list('name', flat=True)
    technician_teams = teams.values_list('name', flat=True)
    stages = models.execute_kw(
        db, uid, password, 'maintenance.stage', 'search_read',
        [[]],
        {'fields': ['id', 'name', 'done']}
    )
    user_tasks = Task.objects.filter(user_id=request.user.id)

    can_create_team = False
    if user.groups.filter(id=2).exists() and not Teams.objects.filter(manager=user).exists():
        can_create_team = True

    tasks = Task.objects.filter(
        Q(maintenance_team_id__in=teams) & Q(stage_id=1)
    )

    manager_team = Teams.objects.filter(manager=user).first()

    if manager_team:
        technician_group = Group.objects.get(name='Technicien')
        members = technician_group.user_set.filter(teams=manager_team)
    else:
        members = []

    context = {
        'can_create_team': can_create_team,
        'user': user,
        'user_groups': user_groups,
        'managed_teams': managed_teams,
        'technician_teams': technician_teams,
        'tasks': tasks,
        'user_tasks': user_tasks,
        'stages': stages,
        'members': members
    }

    return render(request, 'app/technician_members.html', context)

def create_team(request):
    # Ajout des variables similaires à celles dans manager_members
    user = request.user
    user_groups = user.groups.all()
    teams = Teams.objects.filter(members=user)
    managed_teams = Teams.objects.filter(manager=user).values_list('name', flat=True)
    technician_teams = teams.values_list('name', flat=True)
    stages = models.execute_kw(
        db, uid, password, 'maintenance.stage', 'search_read',
        [[]],
        {'fields': ['id', 'name', 'done']}
    )
    user_tasks = Task.objects.filter(user_id=request.user.id)

    can_create_team = False
    if user.groups.filter(id=2).exists() and not Teams.objects.filter(manager=user).exists():
        can_create_team = True

    tasks = Task.objects.filter(
        Q(maintenance_team_id__in=teams) & Q(stage_id=1))

    if request.method == 'POST':
        team_name = request.POST.get('team_name')

        if not Teams.objects.filter(name=team_name).exists():
            new_team_data = {
                'name': team_name,
                'active': True,
            }
            try:
                new_team_id = models.execute_kw(
                    db, uid, password, 'maintenance.team', 'create',
                    [new_team_data]
                )
                if new_team_id:
                    team_id = new_team_id
                    team = Teams.objects.create(id=team_id, name=team_name, manager=request.user)
                    team.members.add(request.user)
                    models.execute_kw(
                        db, uid, password, 'maintenance.team', 'write',
                        [[team_id], {'member_ids': [(4, request.user.id)]}]
                    )
                
                return redirect('home')
            except Fault as e:
                messages.error(request, f"Erreur lors de la création de l'équipe dans Odoo : {e}")
        else:
            messages.error(request, 'Cette équipe existe déjà.')

    context = {
        'can_create_team': can_create_team,
        'user': user,
        'user_groups': user_groups,
        'managed_teams': managed_teams,
        'technician_teams': technician_teams,
        'tasks': tasks,
        'user_tasks': user_tasks,
        'stages': stages,
    }

    return render(request, 'app/create_team.html', context)


def sync_with_odoo():
    # Récupérer les tâches depuis Odoo
    tasks = models.execute_kw(
        db, uid, password,
        'maintenance.request',
        'search_read',
        [[]],
        {'fields': ['id', 'name', 'stage_id', 'maintenance_type', 'user_id', 'priority', 'schedule_date', 'equipment_id', 'description', 'instruction_text', 'maintenance_team_id', 'create_date']}
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
            existing_task.instruction_text = task_data['instruction_text']
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
                instruction_text=task_data['instruction_text'],
                maintenance_team_id=task_data.get('maintenance_team_id', False) and task_data['maintenance_team_id'][0],
                create_date=task_data['create_date'],
                schedule_date=task_data['schedule_date']
            )
            task.save()

    Task.objects.exclude(id__in=odoo_task_ids).delete()

def sync_equipments_from_odoo():
    # Récupérer les équipements depuis Odoo
    equipments = models.execute_kw(
        db, uid, password,
        'maintenance.equipment',
        'search_read',
        [[]],
        {'fields': ['id', 'name', 'maintenance_team_id']}
    )

    # Créer une liste pour stocker les ID des équipements récupérés depuis Odoo
    odoo_equipment_ids = []
    for equipment_data in equipments:
        equipment_id = equipment_data['id']
        odoo_equipment_ids.append(equipment_id)
        existing_equipment = Equipment.objects.filter(id=equipment_id).first()
        if existing_equipment:
            # Mettre à jour l'équipement existant s'il existe déjà dans la base de données locale
            existing_equipment.name = equipment_data['name']
            existing_equipment.maintenance_team_id = equipment_data.get('maintenance_team_id', False) and equipment_data['maintenance_team_id'][0]
            existing_equipment.save()
        else:
            # Créer un nouvel équipement s'il n'existe pas encore dans la base de données locale
            equipment = Equipment(
                id=equipment_id,
                name=equipment_data['name'],
                maintenance_team_id=equipment_data.get('maintenance_team_id', False) and equipment_data['maintenance_team_id'][0]
            )
            equipment.save()

    # Supprimer les équipements locaux qui ne sont pas présents dans Odoo
    Equipment.objects.exclude(id__in=odoo_equipment_ids).delete()

@login_required
def task_list(request):
    sync_equipments_from_odoo()
    sync_with_odoo()
    tasks = Task.objects.all().order_by('create_date','priority')
    manager = request.user
    manager_team = Teams.objects.filter(manager=manager).first()

    if manager_team:
        tasks = Task.objects.filter(maintenance_team_id=manager_team.id)
    else:
        tasks = None

    users = User.objects.all()
    user_groups = request.user.groups.all()

    can_create_team = user_groups.filter(id=2).exists() and not Teams.objects.filter(manager=request.user).exists()

    # Ajout des variables similaires à celles dans create_team
    teams = Teams.objects.filter(members=request.user)
    managed_teams = Teams.objects.filter(manager=request.user).values_list('name', flat=True)
    technician_teams = teams.values_list('name', flat=True)
    stages = models.execute_kw(
        db, uid, password, 'maintenance.stage', 'search_read',
        [[]],
        {'fields': ['id', 'name', 'done']}
    )
    user_tasks = Task.objects.filter(user_id=request.user.id)

    context = {
        'tasks': tasks,
        'users': users,
        'user_groups': user_groups,
        'can_create_team': can_create_team,
        'teams': teams,
        'managed_teams': managed_teams,
        'technician_teams': technician_teams,
        'stages': stages,
        'user_tasks': user_tasks,
    }
    return render(request, 'app/task_list.html', context)


@user_passes_test(is_technicien)
@login_required
def works_orders(request):
    sync_equipments_from_odoo()
    sync_with_odoo()
    user = request.user
    user_groups = user.groups.all()
    teams = Teams.objects.filter(members=user)
    managed_teams = Teams.objects.filter(manager=user).values_list('name', flat=True)
    technician_teams = teams.values_list('name', flat=True)
    stages = models.execute_kw(
        db, uid, password, 'maintenance.stage', 'search_read',
        [[]],
        {'fields': ['id', 'name', 'done']}
    )
    user_tasks = Task.objects.filter(user_id=request.user.id)

    can_create_team = False
    if user.groups.filter(id=2).exists() and not Teams.objects.filter(manager=user).exists():
        can_create_team = True

    tasks = Task.objects.all().order_by('create_date','priority')
    users = User.objects.all()

    context = {
        'can_create_team': can_create_team,
        'users': users,
        'user': user,
        'user_groups': user_groups,
        'managed_teams': managed_teams,
        'technician_teams': technician_teams,
        'tasks': tasks,
        'user_tasks': user_tasks, 
        'stages': stages
    }
    
    return render(request, 'app/all_works_orders.html', context)


@user_passes_test(is_technicien)
@login_required
def my_tasks(request):
    sync_equipments_from_odoo()
    sync_with_odoo()
    user = request.user
    user_groups = user.groups.all()
    teams = Teams.objects.filter(members=user)
    managed_teams = Teams.objects.filter(manager=user).values_list('name', flat=True)
    technician_teams = teams.values_list('name', flat=True)
    stages = models.execute_kw(
        db, uid, password, 'maintenance.stage', 'search_read',
        [[]],
        {'fields': ['id', 'name', 'done']}
    )
    user_tasks = Task.objects.filter(user_id=request.user.id).order_by('schedule_date','priority')

    can_create_team = False
    if user.groups.filter(id=2).exists() and not Teams.objects.filter(manager=user).exists():
        can_create_team = True

    tasks = Task.objects.filter(
        Q(maintenance_team_id__in=teams) & Q(stage_id=1))
    
    users = User.objects.all()

    context = {
        'can_create_team': can_create_team,
        'users': users,
        'user': user,
        'user_groups': user_groups,
        'managed_teams': managed_teams,
        'technician_teams': technician_teams,
        'tasks': tasks,
        'user_tasks': user_tasks, 
        'stages': stages
    }
    
    return render(request, 'app/my_tasks.html', context)


@login_required
def my_account(request):
    sync_equipments_from_odoo()
    sync_with_odoo()
    user = request.user
    user_groups = user.groups.all()
    teams = Teams.objects.filter(members=user)
    managed_teams = Teams.objects.filter(manager=user).values_list('name', flat=True)
    technician_teams = teams.values_list('name', flat=True)
    stages = models.execute_kw(
        db, uid, password, 'maintenance.stage', 'search_read',
        [[]],
        {'fields': ['id', 'name', 'done']}
    )
    user_tasks = Task.objects.filter(user_id=request.user.id)

    can_create_team = False
    if user.groups.filter(id=2).exists() and not Teams.objects.filter(manager=user).exists():
        can_create_team = True

    tasks = Task.objects.filter(
        Q(maintenance_team_id__in=teams) & Q(stage_id=1))
    
    users = User.objects.all()

    context = {
        'can_create_team': can_create_team,
        'users': users,
        'user': user,
        'user_groups': user_groups,
        'managed_teams': managed_teams,
        'technician_teams': technician_teams,
        'tasks': tasks,
        'user_tasks': user_tasks, 
        'stages': stages
    }
    
    return render(request, 'app/my_account.html', context)

@login_required
def tasks_done(request):
    sync_equipments_from_odoo()
    sync_with_odoo()
    user = request.user
    user_groups = user.groups.all()
    teams = Teams.objects.filter(members=user)
    managed_teams = Teams.objects.filter(manager=user).values_list('name', flat=True)
    technician_teams = teams.values_list('name', flat=True)
    stages = models.execute_kw(
        db, uid, password, 'maintenance.stage', 'search_read',
        [[]],
        {'fields': ['id', 'name', 'done']}
    )
    user_tasks = Task.objects.filter(user_id=request.user.id)

    can_create_team = False
    if user.groups.filter(id=2).exists() and not Teams.objects.filter(manager=user).exists():
        can_create_team = True

    tasks = Task.objects.filter(
        Q(maintenance_team_id__in=teams) & Q(stage_id=1))
    
    users = User.objects.all()

    context = {
        'can_create_team': can_create_team,
        'users': users,
        'user': user,
        'user_groups': user_groups,
        'managed_teams': managed_teams,
        'technician_teams': technician_teams,
        'tasks': tasks,
        'user_tasks': user_tasks, 
        'stages': stages
    }
    
    return render(request, 'app/tasks_done.html', context)





@login_required
@user_passes_test(is_technicien)
def take_task(request):
    if request.method == 'POST':
        task_id = request.POST.get('taskId')
        user_id = request.POST.get('userId')

        try:
            user = User.objects.get(id=user_id)
            task = Task.objects.get(id=task_id)
            now = datetime.now()
            formatted_now = now.strftime('%Y-%m-%d %H:%M:%S')

            result = models.execute_kw(
                db, uid, password,
                'maintenance.request', 'write',
                [[int(task_id)], {'stage_id': 2, 'user_id': int(user_id), 'schedule_date': formatted_now}]
            )

            if result:  
                print("La tâche a été mise à jour avec succès.")
                my_tasks, _ = MyTasks.objects.get_or_create(user=user)
                my_tasks.tasks.add(task)
                my_tasks.save()
            else:
                print("La tâche n'a pas pu être mise à jour.")

        except (User.DoesNotExist, Task.DoesNotExist):
            print("L'utilisateur ou la tâche n'existe pas.")



        return redirect('home')  
    else:
        pass

@login_required
@user_passes_test(is_technicien)
def update_task(request):
    if request.method == 'POST':
        task_id = request.POST.get('taskId')
        user_id = request.POST.get('userId')
        stage_id = request.POST.get('stageId')
        print(stage_id)

        try:
            user = User.objects.get(id=user_id)
            task = Task.objects.get(id=task_id)            

            result = models.execute_kw(
                db, uid, password,
                'maintenance.request', 'write',
                [[int(task_id)], {'stage_id': int(stage_id)}]
            )

            if result:  
                print("La tâche a été mise à jour avec succès.")
                my_tasks, _ = MyTasks.objects.get_or_create(user=user)
                my_tasks.tasks.remove(task)
                my_tasks.save()
            else:
                print("La tâche n'a pas pu être mise à jour.")

        except (User.DoesNotExist, Task.DoesNotExist):
            print("L'utilisateur ou la tâche n'existe pas.")



        return redirect('my_tasks')  
    else:
        pass
@login_required
@user_passes_test(is_admin_or_manager)
def edit_member(request, member_id):
    user = User.objects.get(id=member_id)

    current_user = request.user
    user_groups = current_user.groups.all()
    teams = Teams.objects.filter(members=current_user)
    managed_teams = Teams.objects.filter(manager=current_user).values_list('name', flat=True)
    technician_teams = teams.values_list('name', flat=True)
    stages = models.execute_kw(
        db, uid, password, 'maintenance.stage', 'search_read',
        [[]],
        {'fields': ['id', 'name', 'done']}
    )
    user_tasks = Task.objects.filter(user_id=current_user.id)

    can_create_team = False
    if current_user.groups.filter(id=2).exists() and not Teams.objects.filter(manager=current_user).exists():
        can_create_team = True

    tasks = Task.objects.filter(
        Q(maintenance_team_id__in=teams) & Q(stage_id=1))

    if request.method == 'POST':
        user.username = request.POST['username']
        user.email = request.POST['email']
        user.first_name = request.POST['first_name']
        user.last_name = request.POST['last_name']
        new_password = request.POST.get('password', '')
        if new_password:
            user.set_password(new_password)
        vals = {
            'name': user.username,
            'login': user.email,
            'password': user.password,
        }
        models.execute_kw(db, uid, password, 'res.users', 'write', [[member_id], vals])
        user.save()
        if request.user.groups.filter(name='Manager').exists():
            return redirect('technician_members')  
        elif request.user.groups.filter(name='Admin').exists():
            return redirect('manager_members')

    context = {
        'user': user,
        'current_user': current_user,
        'user_groups': user_groups,
        'managed_teams': managed_teams,
        'technician_teams': technician_teams,
        'tasks': tasks,
        'user_tasks': user_tasks,
        'stages': stages,
        'can_create_team': can_create_team,
    }

    return render(request, 'app/edit_member.html', context)


@login_required
@user_passes_test(is_admin_or_manager)
def delete_member(request, member_id):
    user = User.objects.get(id=member_id)
    if request.method == 'POST':
        try:
            team = Teams.objects.filter(manager=user).first()
            if team:
                models.execute_kw(db, uid, password, 'maintenance.team', 'unlink', [[team.id]])
            models.execute_kw(db, uid, password, 'res.users', 'unlink', [[member_id]])
            user.delete()
            if request.user.groups.filter(name='Manager').exists():
                return redirect('technician_members')  
            elif request.user.groups.filter(name='Admin').exists():
                return redirect('manager_members')
        except Exception as e:
            messages.error(request, f"Erreur lors de la suppression de l'utilisateur : {e}")
            return redirect('confirm_delete', member_id=member_id)
    return render(request, 'app/confirm_delete.html', {'user': user})

@login_required
@user_passes_test(is_manager)
def users_without_team(request):
    # Synchronize data with Odoo
    sync_equipments_from_odoo()
    sync_with_odoo()
    
    # Get the current user and their groups
    user = request.user
    user_groups = user.groups.all()

    # Fetch teams related to the current user
    teams = Teams.objects.filter(members=user)
    managed_teams = Teams.objects.filter(manager=user).values_list('name', flat=True)
    technician_teams = teams.values_list('name', flat=True)

    # Fetch stages from Odoo
    stages = models.execute_kw(
        db, uid, password, 'maintenance.stage', 'search_read',
        [[]],
        {'fields': ['id', 'name', 'done']}
    )

    # Get tasks assigned to the current user
    user_tasks = Task.objects.filter(user_id=request.user.id)

    # Determine if the user can create a team
    can_create_team = False
    if user.groups.filter(id=2).exists() and not Teams.objects.filter(manager=user).exists():
        can_create_team = True

    # Fetch tasks for the current user's teams
    tasks = Task.objects.filter(
        Q(maintenance_team_id__in=teams) & Q(stage_id=1))
    
    # Fetch users without teams who are in the Technicien group
    technicien_group = Group.objects.get(name='Technicien')
    users = User.objects.exclude(teams__isnull=False).filter(groups=technicien_group)

    context = {
        'can_create_team': can_create_team,
        'users': users,
        'user': user,
        'user_groups': user_groups,
        'managed_teams': managed_teams,
        'technician_teams': technician_teams,
        'tasks': tasks,
        'user_tasks': user_tasks,
        'stages': stages
    }
    
    return render(request, 'app/users_without_team.html', context)


@login_required
@user_passes_test(is_manager)
def add_to_manager_team(request):
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        user = User.objects.get(id=user_id)
        manager = request.user
        manager_team = Teams.objects.filter(manager=manager).first()
        if manager_team:
            manager_team.members.add(user)
            models.execute_kw(
                db, uid, password, 'maintenance.team', 'write',
                [[manager_team.id], {'member_ids': [(4, user_id)]}]
            )
            messages.success(request, 'Utilisateur ajouté à votre équipe avec succès.')
        else:
            messages.error(request, 'Impossible de trouver votre équipe.')
    
    return redirect('users_without_team')

@login_required
@user_passes_test(is_manager)
def upload_model(request):
    if request.method == 'POST':
        form = UploadModelForm(request.POST, request.FILES)
        if form.is_valid():
            file = form.cleaned_data['file']
            nomenclature = form.cleaned_data['nomenclature']
            equipement = form.cleaned_data['equipement']
            user = request.user  # Assurez-vous d'avoir le user

            try:
                UploadedModel.objects.create(user=user, file=file, nomenclature=nomenclature, equipement=equipement)
                messages.success(request, "Le modèle a été téléchargé avec succès.")
                return redirect('home')  # Rediriger vers la page d'accueil après le succès
            except Exception as e:
                messages.error(request, f"Erreur lors du téléchargement du modèle : {str(e)}")
        else:
            messages.error(request, "Le formulaire n'est pas valide. Veuillez corriger les erreurs.")
    else:
        form = UploadModelForm()
    
    return render(request, 'app/upload_model.html', {'form': form})  # Rendre le formulaire s'il y a une erreur ou si c'est une requête GET

@login_required
@user_passes_test(is_manager)
def model_list(request):
    models = UploadedModel.objects.filter(user=request.user)
    return render(request, 'app/model_list.html', {'models': models})