# Generated by Django 4.1.5 on 2023-07-18 15:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0003_remove_profile_birth_date_alter_profile_bio'),
    ]

    operations = [
        migrations.AlterField(
            model_name='profile',
            name='image',
            field=models.ImageField(default='avatars/avatar.jpg', upload_to='avatars', verbose_name='user avatar'),
        ),
    ]