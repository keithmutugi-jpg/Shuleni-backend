from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import (
    AuthToken, AttendanceRecord, ChatMessage, ChatRoom, Exam, ExamQuestion,
    ExamResult, Member, ResourceFile, ResourceFolder, School,
)


@api_view(['GET'])
def health_check(request):
    return Response({"status": "ok", "message": "Shuleni backend is running"})


def _session_payload(member):
    return {
        "schoolId": member.school_id,
        "schoolName": member.school.name,
        "userId": member.id,
        "name": member.name,
        "role": member.role,
    }


def _member_from_auth_header(request):
    auth = request.headers.get('Authorization', '')
    if not auth.startswith('Token '):
        return None
    key = auth.split(' ', 1)[1].strip()
    if not key:
        return None
    token = AuthToken.objects.filter(key=key).select_related('member', 'member__school').first()
    return token.member if token else None


def _require_member(request):
    member = _member_from_auth_header(request)
    if not member:
        return None, Response({"error": "Invalid or missing token."}, status=401)
    return member, None


def _safe_user(member):
    return {
        "id": member.id,
        "role": member.role,
        "name": member.name,
        "email": member.email,
        "classGroup": member.class_group or None,
        "subjects": member.subjects or None,
        "username": member.username,
    }


@api_view(['POST'])
def register_school(request):
    data = request.data
    school_name = (data.get('schoolName') or '').strip()
    owner_name = (data.get('ownerName') or '').strip()
    email = (data.get('email') or '').strip()
    username = (data.get('username') or '').strip()
    password = data.get('password') or ''
    if not school_name or not owner_name or not username or not password:
        return Response({"error": "All fields are required."}, status=400)
    if len(password) < 6:
        return Response({"error": "Password must be at least 6 characters."}, status=400)
    if School.objects.filter(name__iexact=school_name).exists():
        return Response({"error": "A school with that name already exists — try a more specific name."}, status=400)
    school = School.objects.create(name=school_name)
    owner = Member(school=school, role='owner', name=owner_name, email=email, username=username)
    owner.set_password(password)
    owner.save()
    token = AuthToken.objects.create(member=owner)
    ChatRoom.objects.create(school=school, name='General Announcements', class_group='')
    return Response({
        "school": {"id": school.id, "name": school.name},
        "session": _session_payload(owner),
        "token": token.key,
    }, status=201)


@api_view(['POST'])
def login_view(request):
    data = request.data
    school_needle = (data.get('schoolNameOrId') or '').strip().lstrip('#')
    username = (data.get('username') or '').strip()
    password = data.get('password') or ''
    if not school_needle or not username or not password:
        return Response({"error": "School, username and password are all required."}, status=400)
    school = School.objects.filter(id__iexact=school_needle).first() or School.objects.filter(name__iexact=school_needle).first()
    if not school:
        return Response({"error": "No school matches that name or ID."}, status=400)
    member = Member.objects.filter(school=school, username=username).first()
    if not member or not member.check_password(password):
        return Response({"error": "Incorrect username or password for this school."}, status=400)
    token = AuthToken.objects.create(member=member)
    return Response({"session": _session_payload(member), "token": token.key})


@api_view(['POST'])
def logout_view(request):
    auth = request.headers.get('Authorization', '')
    if auth.startswith('Token '):
        AuthToken.objects.filter(key=auth.split(' ', 1)[1].strip()).delete()
    return Response({"status": "ok"})


@api_view(['GET'])
def session_view(request):
    member, error = _require_member(request)
    if error:
        return error
    return Response({"session": _session_payload(member)})


@api_view(['GET', 'POST'])
def users_view(request):
    member, error = _require_member(request)
    if error:
        return error
    if request.method == 'GET':
        members = Member.objects.filter(school=member.school).order_by('created_at')
        return Response([_safe_user(m) for m in members])
    if member.role != 'owner':
        return Response({"error": "Only the school owner can add students or educators."}, status=403)
    data = request.data
    role = data.get('role')
    name = (data.get('name') or '').strip()
    email = (data.get('email') or '').strip()
    class_group = (data.get('classGroup') or '').strip()
    password = data.get('password') or 'changeme123'
    if role not in ('student', 'educator'):
        return Response({"error": "role must be 'student' or 'educator'."}, status=400)
    if not name or not email:
        return Response({"error": "Name and email are required."}, status=400)
    base_username = email.split('@')[0] or name.lower().replace(' ', '.')
    username = base_username
    suffix = 1
    while Member.objects.filter(school=member.school, username=username).exists():
        suffix += 1
        username = f"{base_username}{suffix}"
    new_member = Member(
        school=member.school, role=role, name=name, email=email,
        class_group=class_group if role == 'student' else '',
        subjects=class_group if role == 'educator' else '', username=username,
    )
    new_member.set_password(password)
    new_member.save()
    result = _safe_user(new_member)
    result["temporaryPassword"] = password
    return Response(result, status=201)


def _resource_payload(folder):
    return {
        "id": folder.id,
        "subject": folder.subject,
        "access": folder.access,
        "files": [{
            "id": f.id,
            "name": f.name,
            "sizeKb": f.size_kb,
            "uploadedAt": f.uploaded_at.isoformat(),
            "url": f.file.url if f.file else None,
        } for f in folder.files.all().order_by('-uploaded_at')],
    }


@api_view(['GET', 'POST'])
def resources_view(request):
    member, error = _require_member(request)
    if error:
        return error
    if request.method == 'GET':
        folders = ResourceFolder.objects.filter(school=member.school).prefetch_related('files').order_by('subject')
        return Response([_resource_payload(f) for f in folders])

    if member.role not in ('owner', 'educator'):
        return Response({"error": "Only educators and the school owner can add resources."}, status=403)
    subject = (request.data.get('subject') or '').strip()
    if not subject:
        return Response({"error": "Subject is required."}, status=400)
    restricted = str(request.data.get('restricted', 'false')).lower() in ('1', 'true', 'yes', 'on')
    folder, _ = ResourceFolder.objects.get_or_create(school=member.school, subject=subject)
    folder.access = 'restricted' if restricted else 'open'
    folder.save(update_fields=['access', 'updated_at'])

    uploaded = request.FILES.get('file')
    file_name = (request.data.get('fileName') or '').strip()
    if not uploaded and not file_name:
        return Response({"error": "Choose a file or provide a file name."}, status=400)

    if uploaded:
        file_obj = ResourceFile.objects.create(
            folder=folder, name=uploaded.name, file=uploaded,
            size_kb=max(1, round(uploaded.size / 1024)), uploaded_by=member,
        )
    else:
        file_obj = ResourceFile.objects.create(
            folder=folder, name=file_name, size_kb=0, uploaded_by=member,
        )
    return Response(_resource_payload(folder), status=201)


@api_view(['GET'])
def attendance_view(request):
    member, error = _require_member(request)
    if error:
        return error
    qs = AttendanceRecord.objects.filter(school=member.school).select_related('submitted_by').order_by('-submitted_at')
    if member.role == 'student':
        qs = qs.filter(class_group=member.class_group)
    return Response([{
        "id": r.id, "date": r.date.isoformat(), "classGroup": r.class_group,
        "subject": r.subject, "counts": r.counts, "roster": r.roster,
        "submittedBy": r.submitted_by.name, "submittedAt": r.submitted_at.isoformat(),
    } for r in qs])


@api_view(['POST'])
def attendance_submit_view(request):
    member, error = _require_member(request)
    if error:
        return error
    if member.role not in ('owner', 'educator'):
        return Response({"error": "Only educators and the school owner can submit attendance."}, status=403)
    data = request.data
    class_group = (data.get('classGroup') or '').strip()
    subject = (data.get('subject') or '').strip()
    date_value = data.get('date')
    roster = data.get('roster') or []
    counts = data.get('counts') or {}
    if not class_group or not subject or not date_value:
        return Response({"error": "Date, class and subject are required."}, status=400)
    record = AttendanceRecord.objects.create(
        school=member.school, date=date_value, class_group=class_group, subject=subject,
        counts=counts, roster=roster, submitted_by=member,
    )
    return Response({
        "id": record.id, "date": record.date.isoformat(), "classGroup": record.class_group,
        "subject": record.subject, "counts": record.counts, "roster": record.roster,
        "submittedBy": member.name, "submittedAt": record.submitted_at.isoformat(),
    }, status=201)


def _exam_payload(exam, include_answers=False):
    questions = []
    for q in exam.questions.all():
        item = {"id": q.id, "prompt": q.prompt, "options": q.options}
        if include_answers:
            item["correctIndex"] = q.correct_index
        questions.append(item)
    return {
        "id": exam.id, "title": exam.title, "minutes": exam.minutes,
        "questions": questions, "createdAt": exam.created_at.isoformat(),
    }


@api_view(['GET', 'POST'])
def exams_view(request):
    member, error = _require_member(request)
    if error:
        return error
    if request.method == 'GET':
        exams = Exam.objects.filter(school=member.school).prefetch_related('questions').order_by('-created_at')
        return Response([_exam_payload(e, include_answers=member.role in ('owner', 'educator')) for e in exams])

    if member.role not in ('owner', 'educator'):
        return Response({"error": "Only educators and the school owner can create exams."}, status=403)
    data = request.data
    title = (data.get('title') or '').strip()
    minutes = int(data.get('minutes') or 0)
    questions = data.get('questions') or []
    if not title:
        return Response({"error": "Exam title is required."}, status=400)
    if minutes < 1:
        return Response({"error": "Time limit must be at least 1 minute."}, status=400)
    if not questions:
        return Response({"error": "Add at least one question."}, status=400)

    with transaction.atomic():
        exam = Exam.objects.create(school=member.school, title=title, minutes=minutes, created_by=member)
        for pos, q in enumerate(questions):
            prompt = (q.get('prompt') or '').strip()
            options = q.get('options') or []
            correct_index = int(q.get('correctIndex', 0))
            if not prompt or len(options) != 4 or any(not str(o).strip() for o in options):
                transaction.set_rollback(True)
                return Response({"error": "Every question must have a prompt and four options."}, status=400)
            if correct_index < 0 or correct_index > 3:
                transaction.set_rollback(True)
                return Response({"error": "Invalid correct answer."}, status=400)
            ExamQuestion.objects.create(exam=exam, prompt=prompt, options=options, correct_index=correct_index, position=pos)
    return Response(_exam_payload(exam, include_answers=True), status=201)


@api_view(['POST'])
def exam_submit_view(request, exam_id):
    member, error = _require_member(request)
    if error:
        return error
    if member.role != 'student':
        return Response({"error": "Only students can submit exams."}, status=403)
    exam = get_object_or_404(Exam.objects.prefetch_related('questions'), id=exam_id, school=member.school)
    if ExamResult.objects.filter(exam=exam, student=member).exists():
        return Response({"error": "You have already submitted this exam."}, status=409)
    data = request.data
    answers = data.get('answers') or {}
    correct = sum(1 for q in exam.questions.all() if str(answers.get(str(q.id), answers.get(q.id, ''))) == str(q.correct_index))
    time_taken = max(0, int(data.get('timeTakenSeconds') or 0))
    violations = max(0, int(data.get('violations') or 0))
    result = ExamResult.objects.create(
        exam=exam, student=member, score=correct, total=exam.questions.count(),
        time_taken_seconds=time_taken, violations=violations,
    )
    return Response({
        "id": result.id, "examId": exam.id, "studentId": member.id,
        "studentName": member.name, "examTitle": exam.title, "score": result.score,
        "total": result.total, "timeTakenSeconds": result.time_taken_seconds,
        "violations": result.violations, "submittedAt": result.submitted_at.isoformat(),
    }, status=201)


@api_view(['GET'])
def exam_results_view(request):
    member, error = _require_member(request)
    if error:
        return error
    qs = ExamResult.objects.filter(exam__school=member.school).select_related('exam', 'student').order_by('-submitted_at')
    if member.role == 'student':
        qs = qs.filter(student=member)
    return Response([{
        "id": r.id, "examId": r.exam_id, "studentId": r.student_id,
        "studentName": r.student.name, "examTitle": r.exam.title, "score": r.score,
        "total": r.total, "timeTakenSeconds": r.time_taken_seconds,
        "violations": r.violations, "submittedAt": r.submitted_at.isoformat(),
    } for r in qs])


def _chat_payload(room):
    return {
        "id": room.id, "name": room.name, "classGroup": room.class_group or None,
        "messages": [{
            "id": m.id, "authorName": m.author.name, "authorRole": m.author.role,
            "text": m.text, "at": m.created_at.isoformat(),
        } for m in room.messages.select_related('author').order_by('created_at')],
    }


@api_view(['GET'])
def chats_view(request):
    member, error = _require_member(request)
    if error:
        return error
    rooms = ChatRoom.objects.filter(school=member.school).prefetch_related('messages__author').order_by('id')
    if member.role == 'student':
        rooms = rooms.filter(Q(class_group='') | Q(class_group=member.class_group))
    return Response([_chat_payload(r) for r in rooms])


@api_view(['POST'])
def chat_message_view(request, room_id):
    member, error = _require_member(request)
    if error:
        return error
    room = get_object_or_404(ChatRoom, id=room_id, school=member.school)
    if member.role == 'student' and room.class_group and room.class_group != member.class_group:
        return Response({"error": "You cannot access this class chat."}, status=403)
    text = (request.data.get('text') or '').strip()
    if not text:
        return Response({"error": "Message cannot be empty."}, status=400)
    message = ChatMessage.objects.create(room=room, author=member, text=text)
    return Response({
        "id": message.id, "authorName": member.name, "authorRole": member.role,
        "text": message.text, "at": message.created_at.isoformat(),
    }, status=201)
