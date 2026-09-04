# Generated migration for Shuleni shared learning data.
import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('api', '0001_initial')]

    operations = [
        migrations.CreateModel(
            name='ChatRoom',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('class_group', models.CharField(blank=True, max_length=100, null=True)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('school', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='chat_rooms', to='api.school')),
            ],
        ),
        migrations.CreateModel(
            name='Exam',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255)),
                ('minutes', models.PositiveIntegerField(default=15)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='created_exams', to='api.member')),
                ('school', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='exams', to='api.school')),
            ],
        ),
        migrations.CreateModel(
            name='ResourceFolder',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('subject', models.CharField(max_length=120)),
                ('access', models.CharField(choices=[('open', 'Open'), ('restricted', 'Restricted')], default='open', max_length=20)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('school', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='resource_folders', to='api.school')),
            ],
            options={'unique_together': {('school', 'subject')}},
        ),
        migrations.CreateModel(
            name='AttendanceRecord',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField()),
                ('class_group', models.CharField(max_length=100)),
                ('subject', models.CharField(max_length=120)),
                ('counts', models.JSONField(default=dict)),
                ('roster', models.JSONField(default=list)),
                ('submitted_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('school', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='attendance_records', to='api.school')),
                ('submitted_by', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='attendance_submissions', to='api.member')),
            ],
        ),
        migrations.CreateModel(
            name='ExamQuestion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('prompt', models.TextField()),
                ('options', models.JSONField(default=list)),
                ('correct_index', models.PositiveSmallIntegerField(default=0)),
                ('position', models.PositiveIntegerField(default=0)),
                ('exam', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='questions', to='api.exam')),
            ],
            options={'ordering': ['position']},
        ),
        migrations.CreateModel(
            name='ResourceFile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('file', models.FileField(blank=True, null=True, upload_to='resources/')),
                ('size_kb', models.PositiveIntegerField(default=0)),
                ('uploaded_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('folder', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='files', to='api.resourcefolder')),
                ('uploaded_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='uploaded_resources', to='api.member')),
            ],
        ),
        migrations.CreateModel(
            name='ChatMessage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('text', models.TextField()),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('author', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='chat_messages', to='api.member')),
                ('room', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='messages', to='api.chatroom')),
            ],
        ),
        migrations.CreateModel(
            name='ExamResult',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('score', models.PositiveIntegerField(default=0)),
                ('total', models.PositiveIntegerField(default=0)),
                ('time_taken_seconds', models.PositiveIntegerField(default=0)),
                ('violations', models.PositiveIntegerField(default=0)),
                ('submitted_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('exam', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='results', to='api.exam')),
                ('student', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='exam_results', to='api.member')),
            ],
            options={'unique_together': {('exam', 'student')}},
        ),
    ]
