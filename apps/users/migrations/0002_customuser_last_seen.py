from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="customuser",
            name="last_seen",
            field=models.DateTimeField(blank=True, null=True, verbose_name="เวลาใช้งานล่าสุด"),
        ),
    ]
