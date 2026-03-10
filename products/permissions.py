from rest_framework.permissions import BasePermission


class IsSeller(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'seller'


class IsOwner(BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.seller == request.user