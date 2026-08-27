from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view
from rest_framework.response import Response
 
from .models import AuthToken, Member, School
 
 
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
    """Pulls the bearer token out of the Authorization header and
    resolves it to a Member. Returns None for a missing header, a
    malformed one, or a token that doesn't match anything — callers
    treat all three the same way (401 Unauthorized)."""
    auth = request.headers.get('Authorization', '')
    if not auth.startswith('Token '):
        return None
    key = auth.split(' ', 1)[1].strip()
    if not key:
        return None
    token = AuthToken.objects.filter(key=key).select_related('member', 'member__school').first()
    return token.member if token else None
 
 
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
 
    school = (
        School.objects.filter(id__iexact=school_needle).first()
        or School.objects.filter(name__iexact=school_needle).first()
    )
    if not school:
        return Response({"error": "No school matches that name or ID."}, status=400)
 
    member = Member.objects.filter(school=school, username=username).first()
    if not member or not member.check_password(password):
        # Deliberately vague — never reveal whether it was the
        # username or the password that didn't match.
        return Response({"error": "Incorrect username or password for this school."}, status=400)
 
    token = AuthToken.objects.create(member=member)
 
    return Response({
        "session": _session_payload(member),
        "token": token.key,
    })
 
 
@api_view(['POST'])
def logout_view(request):
    auth = request.headers.get('Authorization', '')
    if auth.startswith('Token '):
        key = auth.split(' ', 1)[1].strip()
        AuthToken.objects.filter(key=key).delete()
    return Response({"status": "ok"})
 
 
@api_view(['GET'])
def session_view(request):
    member = _member_from_auth_header(request)
    if not member:
        return Response({"error": "Invalid or missing token."}, status=401)
    return Response({"session": _session_payload(member)})
 
 
def _require_member(request):
    """Shared guard for every endpoint below that needs a logged-in
    user. Returns (member, None) on success, or (None, error_response)
    if the request isn't authenticated — callers just do:
        member, error = _require_member(request)
        if error:
            return error
    """
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
 
 
@api_view(['GET', 'POST'])
def users_view(request):
    member, error = _require_member(request)
    if error:
        return error
 
    if request.method == 'GET':
        # Always scoped to the caller's own school — this is what
        # keeps two schools' rosters from ever mixing.
        members = Member.objects.filter(school=member.school).order_by('created_at')
        return Response([_safe_user(m) for m in members])
 
    if member.role != 'owner':
        return Response({"error": "Only the school owner can add students or educators."}, status=403)
 
    data = request.data
    role = data.get('role')
    name = (data.get('name') or '').strip()
    email = (data.get('email') or '').strip()
    class_group = (data.get('classGroup') or '').strip()
 
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
        school=member.school,
        role=role,
        name=name,
        email=email,
        class_group=class_group if role == 'student' else '',
        subjects=class_group if role == 'educator' else '',
        username=username,
    )
    new_member.set_password('changeme123')
    new_member.save()
 
    return Response(_safe_user(new_member), status=201)
 