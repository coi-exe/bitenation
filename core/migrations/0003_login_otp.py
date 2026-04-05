from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_email_verification'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='otp_code',
            field=models.CharField(blank=True, default='', max_length=6),
        ),
        migrations.AddField(
            model_name='user',
            name='otp_expires',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
