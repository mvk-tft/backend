from rest_framework.permissions import BasePermission


class IsSelf(BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj == request.user


class IsAdmin(BasePermission):
    def has_object_permission(self, request, view, obj):
        return request.user and request.user.is_staff
