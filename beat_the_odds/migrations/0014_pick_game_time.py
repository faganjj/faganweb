# Generated by Django 4.1.5 on 2023-04-24 20:37

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('beat_the_odds', '0013_oddscount'),
    ]

    operations = [
        migrations.AddField(
            model_name='pick',
            name='game_time',
            field=models.TimeField(default=django.utils.timezone.now),
            preserve_default=False,
        ),
    ]
