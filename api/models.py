import secrets

from django.contrib.auth.hashers import make_password, check_password
from django.db import models
from django.utils import timezone


def generate_school_id():
    return f"SCH-{secrets.token_hex(3).upper()}"


class School(models.Model):
    id = models.CharField(primary_key=True, max_length=20, default=generate_school_id, editable=False)
    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.name} ({self.id})"


class Member(models.Model):
    ROLE_CHOICES = [
        ("owner", "Owner"),
        ("educator", "Educator"),
        ("student", "Student"),
    ]

    school = models.ForeignKey(School, related_name="members", on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    name = models.CharField(max_length=255)
    email = models.EmailField(blank=True)
    username = models.CharField(max_length=150)
    password_hash = models.CharField(max_length=255)
    class_group = models.CharField(max_length=100, blank=True)  # students
    subjects = models.CharField(max_length=255, blank=True)  # educators
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ("school", "username")

    def set_password(self, raw_password):
        self.password_hash = make_password(raw_password)

    def check_password(self, raw_password):
        return check_password(raw_password, self.password_hash)

    def __str__(self):
        return f"{self.name} ({self.role}) @ {self.school_id}"

def generate_token_key():
    return secrets.token_hex(32)


class AuthToken(models.Model):
    key = models.CharField(primary_key=True, max_length=64, default=generate_token_key)
    member = models.ForeignKey(Member, related_name="tokens", on_delete=models.CASCADE)
    created_at = models.DateTimeField(default=timezone.now)