from django.db import migrations, models


class Migration(migrations.Migration):
    """Create the ShortLink table."""

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="ShortLink",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("code", models.SlugField(max_length=32, unique=True)),
                ("target_url", models.URLField(max_length=2048)),
                ("clicks", models.PositiveIntegerField(default=0)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "ordering": ("-clicks", "-created_at"),
            },
        ),
    ]