# Generated by Django 4.1.5 on 2023-12-23 00:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('beat_the_odds', '0019_game_game_id_pick_game_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='pick',
            name='time_stamp',
            field=models.CharField(blank=True, max_length=30),
        ),
    ]
