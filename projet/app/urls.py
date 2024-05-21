# urls.py
from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', views.user_login, name='login'),
    path('home/', views.home, name='home'),
    path('add_manager/', views.add_manager, name='add_manager'),
    path('manager_members/', views.manager_members, name='manager_members'),
    path('add_technician/', views.add_technician, name='add_technician'),
    path('technician_members/', views.technician_members, name='technician_members'),
    path('create_team/', views.create_team, name='create_team'),
    path('task_list/', views.task_list, name='task_list'),
    path('take_task/', views.take_task, name='take_task'),
    path('update_task/', views.update_task, name='update_task'),
    path('delete/<int:member_id>/', views.delete_member, name='delete_member'),
    path('edit/<int:member_id>/', views.edit_member, name='edit_member'),
    path('works_orders/', views.works_orders, name='works_orders'),
    path('my_tasks/', views.my_tasks, name='my_tasks'),
    path('logout/', auth_views.LogoutView.as_view(next_page='/'), name='logout'),
    path('users_without_team.html/', views.users_without_team, name='users_without_team'),
    path('add_to_manager_team/', views.add_to_manager_team, name='add_to_manager_team'),
    path('my_account/', views.my_account, name='my_account'),
    
]
