# Generated by Django 5.1.2 on 2024-10-14 00:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('attendance', '0004_alter_monthperiod_month_session_membersessionlink'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='membersessionlink',
            options={'verbose_name': 'Member - Session Link', 'verbose_name_plural': 'Member - Session Links'},
        ),
        migrations.AlterModelOptions(
            name='monthperiod',
            options={'verbose_name': 'Month', 'verbose_name_plural': 'Months'},
        ),
        migrations.AlterField(
            model_name='member',
            name='last_name',
            field=models.CharField(max_length=100, null=True),
        ),
        migrations.AlterField(
            model_name='session',
            name='date',
            field=models.DateField(),
        ),
    ]
