# Generated by Django 4.2.16 on 2024-11-11 22:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('leaderboard', '0003_alter_matchplayer_mu_alter_matchplayer_rank_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='match',
            name='message_id',
            field=models.CharField(max_length=256, null=True),
        ),
    ]
