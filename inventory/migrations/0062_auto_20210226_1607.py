# Generated by Django 3.1.7 on 2021-02-26 21:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0061_auto_20210127_1547'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='profile',
            name='stripe_customer_id',
        ),
        migrations.RemoveField(
            model_name='profile',
            name='stripe_subscription_id',
        ),
        migrations.RemoveField(
            model_name='profile',
            name='subscription',
        ),
        migrations.AddField(
            model_name='profile',
            name='paddle_cancel_url',
            field=models.URLField(blank=True, help_text='Self-service cancel URL'),
        ),
        migrations.AddField(
            model_name='profile',
            name='paddle_cancellation_date',
            field=models.DateField(blank=True, help_text='When a canceled subscription becomes inactive.', null=True),
        ),
        migrations.AddField(
            model_name='profile',
            name='paddle_subscription_id',
            field=models.IntegerField(blank=True, help_text='Unique for each user.', null=True),
        ),
        migrations.AddField(
            model_name='profile',
            name='paddle_subscription_plan_id',
            field=models.IntegerField(blank=True, help_text='Which of our defined plans.', null=True),
        ),
        migrations.AddField(
            model_name='profile',
            name='paddle_update_url',
            field=models.URLField(blank=True, help_text='Self-service update URL'),
        ),
        migrations.AddField(
            model_name='profile',
            name='paddle_user_id',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='profile',
            name='subscription_status',
            field=models.CharField(choices=[('none', 'Never had a subscription'), ('active', 'Subscribed'), ('trialing', 'Trial period'), ('past_due', 'Past-Due'), ('paused', 'Paused'), ('deleted', 'Canceled')], default='none', max_length=20),
        ),
    ]