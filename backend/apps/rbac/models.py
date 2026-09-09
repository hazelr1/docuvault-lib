from django.conf import settings
from django.db import models


class Role(models.Model):
    STUDENT = "student"
    FACULTY = "faculty"
    ADMINISTRATOR = "administrator"

    ROLE_CHOICES = [
        (STUDENT, "Student"),
        (FACULTY, "Faculty"),
        (ADMINISTRATOR, "Administrator"),
    ]

    name = models.CharField(max_length=32, choices=ROLE_CHOICES, unique=True)
    description = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return self.name


class UserRole(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="role_bindings")
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name="user_bindings")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["user", "role"], name="uniq_user_role")]

    def __str__(self):
        return f"{self.user_id}:{self.role_id}"
