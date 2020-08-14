import os
import json

from django.core.exceptions import ObjectDoesNotExist
from django.utils.decorators import method_decorator
from django.http import FileResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import DjangoModelPermissions

from fastrunner.utils import response
from fastrunner.utils.decorator import request_log
from fastrunner.utils.writeExcel import write_excel_log
from fastrunner.utils.permissions import IsBelongToProject
from fastrunner import models
from FasterRunner.settings import MEDIA_ROOT


class DownloadView(APIView):
    """下载文件接口
    """
    # permission_classes = (DjangoModelPermissions, IsBelongToProject)
    @method_decorator(request_log(level='DEBUG'))
    def post(self, request, **kwargs):
        """下载文件
            请求参数：{
                fileType: int (1:testdata, 2: report_excel 3: report_html)
                id: int,
                project: int
            }
        """
        try:
            file_type = int(request.data["fileType"])
            idno = int(request.data["id"])
            project = int(request.data["project"])
        except KeyError:
            return Response(response.KEY_MISS, status=status.HTTP_400_BAD_REQUEST)
        try:
            if file_type == 1:
                fileObject = models.ModelWithFileField.objects.get(project_id=project, id=idno)
                filename = fileObject.name
                filepath = os.path.join(MEDIA_ROOT, str(fileObject.file))
            else:
                fileObject = models.ReportDetail.objects.get(project_id=project, report_id=idno)
                filename = fileObject.name
                summary = json.loads(fileObject.summary)
                filepath = write_excel_log(summary)

            fileresponse = FileResponse(open(filepath, 'rb'))
            fileresponse["Content-Type"] = "application/octet-stream"
            fileresponse["Content-Disposition"] = "attachment;filename={}".format(filename)
            return fileresponse

        except ObjectDoesNotExist:
            return Response(response.FILE_DOWNLOAD_FAIL, status=status.HTTP_400_BAD_REQUEST)
