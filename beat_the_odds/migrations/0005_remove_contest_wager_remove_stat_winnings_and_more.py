# Generated by Django 4.1.5 on 2023-03-20 18:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('beat_the_odds', '0004_alter_game_odds_away_alter_game_odds_home_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='contest',
            name='wager',
        ),
        migrations.RemoveField(
            model_name='stat',
            name='winnings',
        ),
        migrations.AddField(
            model_name='contest',
            name='complete',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='stat',
            name='points',
            field=models.IntegerField(default=0),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='contest',
            name='active',
            field=models.BooleanField(default=False),
        ),
    ]
