from django.contrib import admin
from .models import Teams, Task, MyTasks

# Enregistrer le modèle Teams dans l'interface d'administration
admin.site.register(Teams)
admin.site.register(Task)
admin.site.register(MyTasks)


