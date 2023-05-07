# Generated by Django 4.1.5 on 2023-04-28 15:56

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('app', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='room',
            name='messages',
        ),
        migrations.RemoveField(
            model_name='room',
            name='users',
        ),
        migrations.AddField(
            model_name='room',
            name='messages',
            field=models.ManyToManyField(to='app.message'),
        ),
        migrations.AddField(
            model_name='room',
            name='users',
            field=models.ManyToManyField(to=settings.AUTH_USER_MODEL),
        ),
    ]