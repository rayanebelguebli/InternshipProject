from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.contrib.auth.models import User, Group
from .models import Teams, Task, MyTasks
from django.db.models import Q
import xmlrpc.client

url = 'http://localhost:8069'
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
    sync_with_odoo()
    user = request.user
    user_groups = user.groups.all()
    teams = Teams.objects.filter(members=user)
    managed_teams = Teams.objects.filter(manager=user).values_list('name', flat=True)
    technician_teams = teams.values_list('name', flat=True)
    stages = models.execute_kw(
        db, uid, password, 'maintenance.stage', 'search_read',
        [[]],
        {'fields': ['id', 'name']}
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
    if request.method == 'POST':
        signup_username = request.POST.get('username')
        signup_email = request.POST.get('email')
        signup_password = request.POST.get('password')
        group_name = 'Manager' 
        
        if not User.objects.filter(username=signup_username).exists():
            new_user_data = {
                'name': signup_username,  
                'login': signup_email,
                'password': signup_password
            }
            new_user_id = models.execute_kw(db, uid, password, 'res.users', 'create', [new_user_data])
        
            if new_user_id:
                user_id = new_user_id
                user = User.objects.create_user(id=user_id, username=signup_username, email=signup_email, password=signup_password)
                messages.success(request, 'Utilisateur ajouté avec succès.')
                group = Group.objects.get(name=group_name)
                user.groups.add(group)
            else:
                messages.error(request, 'Erreur lors de la création de l\'utilisateur.')
        else:
            messages.error(request, 'Cet utilisateur existe déjà.')

        return redirect('home')  

    return render(request, 'app/add_manager.html')

@login_required
@user_passes_test(is_admin)
def manager_members(request):
    manager_group = Group.objects.get(name='Manager')
    members = manager_group.user_set.all()
    return render(request, 'app/manager_members.html', {'members': members})

@login_required
@user_passes_test(is_manager)
def add_technician(request):
    if request.method == 'POST':
        signup_username = request.POST.get('username')
        signup_email = request.POST.get('email')
        signup_password = request.POST.get('password')
        group_name = 'Technicien'

        if not User.objects.filter(username=signup_username).exists():
            new_user_data = {
                'name': signup_username,  
                'login': signup_email,
                'password': signup_password
            }
            new_user_id = models.execute_kw(db, uid, password, 'res.users', 'create', [new_user_data])
        
            if new_user_id:
                user_id = new_user_id
                user = User.objects.create_user(id=user_id, username=signup_username, email=signup_email, password=signup_password)
                messages.success(request, 'Utilisateur ajouté avec succès.')
                group = Group.objects.get(name=group_name)
                user.groups.add(group)

                manager = request.user
                manager_team = Teams.objects.filter(manager=manager).first()
                if manager_team:
                    manager_team.members.add(user)
                    models.execute_kw(
                    db, uid, password, 'maintenance.team', 'write',
                    [[manager_team.id], {'member_ids': [(4, user_id)]}])
                    messages.success(request, 'Utilisateur ajouté à votre équipe avec succès.')
                else:
                    messages.error(request, 'Impossible de trouver votre équipe.')

            else:
                messages.error(request, 'Erreur lors de la création de l\'utilisateur.')
        else:
            messages.error(request, 'Cet utilisateur existe déjà.')

        return redirect('home')

    return render(request, 'app/add_technician.html')

@login_required
@user_passes_test(is_manager)
def technician_members(request):
    manager = request.user
    manager_team = Teams.objects.filter(manager=manager).first()

    if manager_team:
        technician_group = Group.objects.get(name='Technicien')
        members = technician_group.user_set.filter(teams=manager_team)

        return render(request, 'app/technician_members.html', {'members': members})
    else:
        return render(request, 'app/technician_members.html', {'members': []})

@login_required
@user_passes_test(is_manager)
def create_team(request):
    if request.method == 'POST':
        team_name = request.POST.get('team_name')
        
        if not Teams.objects.filter(name=team_name).exists():
            new_team_data = {
            'name': team_name,  
            'active': True,  
        }
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
        else:
            messages.error(request, 'Cet équipe existe déjà.')

    return render(request, 'app/create_team.html')

def sync_with_odoo():
    # Récupérer les tâches depuis Odoo
    tasks = models.execute_kw(
        db, uid, password,
        'maintenance.request',
        'search_read',
        [[]],
        {'fields': ['id', 'name', 'stage_id', 'maintenance_type', 'user_id', 'priority', 'schedule_date', 'equipment_id', 'description', 'instruction_text', 'maintenance_team_id']}
    )

    # Créer une liste pour stocker les ID des tâches récupérées depuis Odoo
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
                maintenance_team_id=task_data.get('maintenance_team_id', False) and task_data['maintenance_team_id'][0]
            )
            task.save()

    Task.objects.exclude(id__in=odoo_task_ids).delete()

@login_required
def task_list(request):
    sync_with_odoo()
    tasks = Task.objects.all()
    manager = request.user
    manager_team = Teams.objects.filter(manager=manager).first()

    if manager_team:
        tasks = Task.objects.filter(maintenance_team_id=manager_team.id)
    else:
        tasks = None
    users = User.objects.all()  
    context = {
        'tasks': tasks,
        'users': users
    }
    return render(request, 'app/task_list.html', context)

@login_required
@user_passes_test(is_technicien)
def take_task(request):
    if request.method == 'POST':
        task_id = request.POST.get('taskId')
        user_id = request.POST.get('userId')

        try:
            user = User.objects.get(id=user_id)
            task = Task.objects.get(id=task_id)

            result = models.execute_kw(
                db, uid, password,
                'maintenance.request', 'write',
                [[int(task_id)], {'stage_id': 2, 'user_id': int(user_id)}]
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

def sync_teams_with_odoo():
    teams_data = models.execute_kw(db, uid, password, 'maintenance.team', 'search_read', [[]], {'fields': ['id', 'name', 'member_ids']})
    print(teams_data)
    for team_data in teams_data:
        team_id = team_data.get('id')
        print(team_id)
        team_name = team_data.get('name')
        print(team_name)
        member_ids = team_data.get('member_ids')
        print(member_ids)

        team_members = User.objects.filter(id__in=member_ids)

        existing_team, created = Teams.objects.get_or_create(id=team_id, defaults={'name': team_name})

        existing_team.name = team_name
        existing_team.members.clear()  
        existing_team.members.add(*team_members)  
        existing_team.save()


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
    return render(request, 'app/edit_member.html', {'user': user})

@login_required
@user_passes_test(is_admin_or_manager)
def delete_member(request, member_id):
    user = User.objects.get(id=member_id)
    if request.method == 'POST':
        models.execute_kw(db, uid, password, 'res.users', 'unlink', [[member_id]])
        user.delete()
        if request.user.groups.filter(name='Manager').exists():
            return redirect('technician_members')  
        elif request.user.groups.filter(name='Admin').exists():
            return redirect('manager_members')
    return render(request, 'app/confirm_delete.html', {'user': user})