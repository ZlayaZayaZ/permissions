from rest_framework.permissions import BasePermission


class IsOwnerOrReadOnly(BasePermission):

    def has_permission(self, request, view):
        if request.user.is_authenticated:
            return True
        return False

    def has_object_permission(self, request, view, obj):
        if request.method == 'GET' or request.user.is_staff is True:
            return True
        return request.user.id == obj.creator_id


class Draft(BasePermission):

    def has_object_permission(self, request, view, obj):
        if request.user.id != obj.creator_id and obj.draft is True:
            return False
        return True

