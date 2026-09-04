import secrets

from django.db import models
from django.utils import timezone
from django.contrib.auth.hashers import make_password, check_password


def generate_school_id():
    return f"SCH-{secrets.token_hex(3).upper()}"


class School(models.Model):
    id = models.CharField(primary_key=True, max_length=20, default=generate_school_id, editable=False)
    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.name} ({self.id})"


class Member(models.Model):
    ROLE_CHOICES = [("owner", "Owner"), ("educator", "Educator"), ("student", "Student")]
    school = models.ForeignKey(School, related_name="members", on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    name = models.CharField(max_length=255)
    email = models.EmailField(blank=True)
    username = models.CharField(max_length=150)
    password_hash = models.CharField(max_length=255)
    class_group = models.CharField(max_length=100, blank=True)
    subjects = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ("school", "username")

    def set_password(self, raw_password):
        self.password_hash = make_password(raw_password)

    def check_password(self, raw_password):
        return check_password(raw_password, self.password_hash)


def generate_token_key():
    return secrets.token_hex(32)


class AuthToken(models.Model):
    key = models.CharField(primary_key=True, max_length=64, default=generate_token_key)
    member = models.ForeignKey(Member, related_name="tokens", on_delete=models.CASCADE)
    created_at = models.DateTimeField(default=timezone.now)


class ResourceFolder(models.Model):
    school = models.ForeignKey(School, related_name="resource_folders", on_delete=models.CASCADE)
    subject = models.CharField(max_length=120)
    access = models.CharField(max_length=20, choices=[("open", "Open"), ("restricted", "Restricted")], default="open")
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("school", "subject")


class ResourceFile(models.Model):
    folder = models.ForeignKey(ResourceFolder, related_name="files", on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    file = models.FileField(upload_to="resources/", blank=True, null=True)
    size_kb = models.PositiveIntegerField(default=0)
    uploaded_by = models.ForeignKey(Member, related_name="uploaded_resources", on_delete=models.SET_NULL, null=True)
    uploaded_at = models.DateTimeField(default=timezone.now)


class Exam(models.Model):
    school = models.ForeignKey(School, related_name="exams", on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    minutes = models.PositiveIntegerField(default=15)
    created_by = models.ForeignKey(Member, related_name="created_exams", on_delete=models.PROTECT)
    created_at = models.DateTimeField(default=timezone.now)


class ExamQuestion(models.Model):
    exam = models.ForeignKey(Exam, related_name="questions", on_delete=models.CASCADE)
    prompt = models.TextField()
    options = models.JSONField(default=list)
    correct_index = models.PositiveSmallIntegerField(default=0)
    position = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["position"]


class ExamResult(models.Model):
    exam = models.ForeignKey(Exam, related_name="results", on_delete=models.CASCADE)
    student = models.ForeignKey(Member, related_name="exam_results", on_delete=models.CASCADE)
    score = models.PositiveIntegerField(default=0)
    total = models.PositiveIntegerField(default=0)
    time_taken_seconds = models.PositiveIntegerField(default=0)
    violations = models.PositiveIntegerField(default=0)
    submitted_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ("exam", "student")


class AttendanceRecord(models.Model):
    school = models.ForeignKey(School, related_name="attendance_records", on_delete=models.CASCADE)
    date = models.DateField()
    class_group = models.CharField(max_length=100)
    subject = models.CharField(max_length=120)
    counts = models.JSONField(default=dict)
    roster = models.JSONField(default=list)
    submitted_by = models.ForeignKey(Member, related_name="attendance_submissions", on_delete=models.PROTECT)
    submitted_at = models.DateTimeField(default=timezone.now)


class ChatRoom(models.Model):
    school = models.ForeignKey(School, related_name="chat_rooms", on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    class_group = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)


class ChatMessage(models.Model):
    room = models.ForeignKey(ChatRoom, related_name="messages", on_delete=models.CASCADE)
    author = models.ForeignKey(Member, related_name="chat_messages", on_delete=models.CASCADE)
    text = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)
