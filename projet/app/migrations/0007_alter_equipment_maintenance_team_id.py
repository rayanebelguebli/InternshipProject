# Generated by Django 4.2.11 on 2024-05-17 14:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0006_alter_task_equipment_id'),
    ]

    operations = [
        migrations.AlterField(
            model_name='equipment',
            name='maintenance_team_id',
            field=models.IntegerField(null=True),
        ),
    ]
