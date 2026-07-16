from django.db import migrations


def grant_view_order(apps, schema_editor):
    """The "Sales Team" group (accounts/migrations/0002) only ever
    granted Product permissions — nobody but a superuser could view an
    Order at all until now. Module 14 adds the invoice-download view,
    which needs a real permission to gate on, so sales reps and managers
    get it here rather than the view falling back to "superuser only."
    """
    Group = apps.get_model("auth", "Group")
    Permission = apps.get_model("auth", "Permission")
    ContentType = apps.get_model("contenttypes", "ContentType")

    order_ct, _ = ContentType.objects.get_or_create(app_label="orders", model="order")
    permission, _ = Permission.objects.get_or_create(
        content_type=order_ct,
        codename="view_order",
        defaults={"name": "Can view order"},
    )

    group = Group.objects.filter(name="Sales Team").first()
    if group:
        group.permissions.add(permission)


def revoke_view_order(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    Permission = apps.get_model("auth", "Permission")

    group = Group.objects.filter(name="Sales Team").first()
    if group:
        group.permissions.filter(content_type__app_label="orders", codename="view_order").delete()


class Migration(migrations.Migration):

    dependencies = [
        ("orders", "0001_initial"),
        ("accounts", "0002_create_sales_team_group"),
    ]

    operations = [
        migrations.RunPython(grant_view_order, revoke_view_order),
    ]
