# Generated by Django 5.1.2 on 2024-10-14 00:18

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('attendance', '0005_alter_membersessionlink_options_and_more'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='member',
            unique_together={('first_name', 'last_name', 'email')},
        ),
    ]