import json

from django.shortcuts import render_to_response
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet, mixins
from rest_framework.permissions import DjangoModelPermissions
from rest_framework import status

from FasterRunner import pagination
from fastrunner import models, serializers
from fastrunner.utils.permissions import IsBelongToProject


class ReportView(GenericViewSet, mixins.RetrieveModelMixin, mixins.ListModelMixin, mixins.DestroyModelMixin):
    """
    测试报告视图
    """
    serializer_class = serializers.ReportSerializer
    pagination_class = pagination.MyPageNumberPagination
    permission_classes = (DjangoModelPermissions, IsBelongToProject)

    def get_queryset(self):
        project = self.request.query_params['project']
        if self.action == 'list':
            search = self.request.query_params["search"]
            return models.Report.objects.filter(project__id=project, name__contains=search).order_by('-update_time')
        return models.Report.objects.filter(project__id=project).order_by('-update_time')

    def destroy(self, request, *args, **kwargs):
        if kwargs.get('pk') and int(kwargs['pk']) != -1:
            instance = self.get_object()
            self.perform_destroy(instance)
        elif request.data:
            for content in request.data:
                self.kwargs['pk'] = content['id']
                instance = self.get_object()
                self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        report_detail = models.ReportDetail.objects.get(report=instance)
        summary = json.loads(report_detail.summary, encoding="utf-8")
        summary["html_report_name"] = instance.name
        return render_to_response('report_template.html', summary)
