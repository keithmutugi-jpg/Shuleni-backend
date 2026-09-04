from django.db import migrations
from django.contrib.auth.hashers import make_password


def seed_demo(apps, schema_editor):
    School = apps.get_model('api', 'School')
    Member = apps.get_model('api', 'Member')
    ResourceFolder = apps.get_model('api', 'ResourceFolder')
    ResourceFile = apps.get_model('api', 'ResourceFile')
    ChatRoom = apps.get_model('api', 'ChatRoom')
    Exam = apps.get_model('api', 'Exam')
    ExamQuestion = apps.get_model('api', 'ExamQuestion')

    school, created = School.objects.get_or_create(id='SCH-004', defaults={'name': 'Greenfield Academy'})
    if not created:
        return

    owner = Member.objects.create(
        school=school, role='owner', name='Kevin Wanjiru',
        username='owner', email='owner@greenfield.ac.ke',
        password_hash=make_password('owner123')
    )
    teacher = Member.objects.create(
        school=school, role='educator', name='Teacher John',
        username='teacher.john', email='john@greenfield.ac.ke',
        subjects='Mathematics, Physics', password_hash=make_password('teacher123')
    )
    students = []
    for i, (name, username, email) in enumerate([
        ('Amara Osei', 'amara.osei', 'amara@greenfield.ac.ke'),
        ('Brian Mwangi', 'brian.mwangi', 'brian@greenfield.ac.ke'),
        ('Cynthia Achieng', 'cynthia.achieng', 'cynthia@greenfield.ac.ke'),
        ('David Kariuki', 'david.kariuki', 'david@greenfield.ac.ke'),
        ('Esther Nalwoga', 'esther.nalwoga', 'esther@greenfield.ac.ke'),
    ], start=41):
        students.append(Member.objects.create(
            school=school, role='student', name=name, username=username,
            email=email, class_group='Form 3B', password_hash=make_password('student123')
        ))

    folder = ResourceFolder.objects.create(school=school, subject='Mathematics', access='open')
    ResourceFile.objects.create(folder=folder, name='Chapter 4 — Quadratic Equations.pdf', size_kb=820, uploaded_by=teacher)

    ChatRoom.objects.create(school=school, name='Form 3B Mathematics', class_group='Form 3B')
    ChatRoom.objects.create(school=school, name='General Announcements', class_group='')

    exam = Exam.objects.create(school=school, title='Mathematics — Form 3B Practice', minutes=15, created_by=teacher)
    ExamQuestion.objects.create(
        exam=exam, prompt='Solve for x: 2x² − 8 = 0',
        options=['x = 2', 'x = 4', 'x = 8', 'x = 16'], correct_index=0, position=0
    )
    ExamQuestion.objects.create(
        exam=exam, prompt='What is 5 × 6?',
        options=['11', '20', '30', '56'], correct_index=2, position=1
    )


class Migration(migrations.Migration):
    dependencies = [('api', '0002_learning_domains')]
    operations = [migrations.RunPython(seed_demo, migrations.RunPython.noop)]
