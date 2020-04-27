from rest_framework.permissions import BasePermission


class IsMatchedUser(BasePermission):
    def has_object_permission(self, request, view, obj):
        user = request.user
        if not user:
            return False
        if user.is_staff:
            return True
        if not user.company:
            return False
        if not obj.inner_shipment:
            return False
        if not obj.outer_shipment:
            return False
        return obj.inner_shipment.company == user.company or obj.outer_shipment.company == user.company
