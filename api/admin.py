from django.contrib import admin

from .models import AuthToken, Member, School


@admin.register(School)
class SchoolAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "created_at")


@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    list_display = ("name", "username", "role", "school", "created_at")
    list_filter = ("role", "school")


@admin.register(AuthToken)
class AuthTokenAdmin(admin.ModelAdmin):
    list_display = ("key", "member", "created_at")