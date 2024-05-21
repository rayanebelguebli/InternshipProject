# Generated by Django 4.2.11 on 2024-05-21 14:06

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('app', '0007_alter_equipment_maintenance_team_id'),
    ]

    operations = [
        migrations.CreateModel(
            name='UploadedModel',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('file', models.FileField(upload_to='uploaded_models/')),
                ('nomenclature', models.CharField(max_length=100)),
                ('source', models.CharField(blank=True, max_length=100)),
                ('equipement', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='app.equipment')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]