from django.db import migrations


def seed_roles(apps, schema_editor):
    Role = apps.get_model("rbac", "Role")
    for role_name in ["student", "faculty", "administrator"]:
        Role.objects.get_or_create(name=role_name)


def reverse_seed_roles(apps, schema_editor):
    Role = apps.get_model("rbac", "Role")
    Role.objects.filter(name__in=["student", "faculty", "administrator"]).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("rbac", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_roles, reverse_seed_roles),
    ]
