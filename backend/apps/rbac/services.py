from apps.rbac.models import Role


def user_role_names(user):
    if not user.is_authenticated:
        return set()
    return set(
        user.role_bindings.select_related("role").values_list("role__name", flat=True)
    )


def is_administrator(user):
    if not user.is_authenticated:
        return False
    if user.is_superuser or user.is_staff:
        return True
    return Role.ADMINISTRATOR in user_role_names(user)
