# -*- coding: utf-8 -*-
from rest_framework import permissions
from django.contrib.auth import get_user_model
from rest_framework import exceptions
from rest_framework import status

from fastrunner.models import LockFiles

UserModel = get_user_model()


class IsBelongToProject(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        """
        Return `True` if permission is granted, `False` otherwise.
        """
        if request.user.is_superuser:
            return True
        project_id_list = UserModel.objects.filter(id=request.user.id).values_list('belong_project', flat=True)
        try:
            project_id = request.data['project']
        except Exception as e:
            project_id = request.query_params['project']
        if int(project_id) in [_ for _ in project_id_list]:
            return True
        return False


def _check_is_locked(project_id, lock_type, file_id):
    lock_queryset = LockFiles.objects.filter(project_id=project_id, lock_type=lock_type, file_id=file_id)
    if lock_queryset:
        raise exceptions.NotAcceptable(detail='该文件被已被锁定，无法更新或删除')
