import datetime
import json
import os

from django.core.exceptions import ObjectDoesNotExist
from django.http import FileResponse, HttpResponse
from django.utils.decorators import method_decorator
from rest_framework import status
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from FasterRunner.settings import MEDIA_ROOT
from fastrunner import models
from fastrunner.utils import response
from fastrunner.utils.decorator import request_log
from fastrunner.utils.writeExcel import write_excel_log, export_apis


class DownloadView(GenericViewSet):
    """下载文件接口
    """

    # permission_classes = (DjangoModelPermissions, IsBelongToProject)
    @method_decorator(request_log(level='DEBUG'))
    def post(self, request, **kwargs):
        """下载文件
            请求参数：{
                fileType: int (1:testdata, 2: report_excel 3: report_html 4: api_templates)
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
            elif file_type == 4:
                fileObject = models.APITemplateFile.objects.get(project_id=project, id=idno)
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

    @method_decorator(request_log(level='DEBUG'))
    def put(self, request):
        """批量下载接口

        """
        project_id = request.data.get('project', 0)
        relation = request.data.get('relation', 0)
        apis = models.API.objects.filter(project=project_id, relation=relation)
        data = []
        for api in apis:
            body = eval(api.body)
            body.update(body['request'])
            desc = body.get('desc', {})
            id = api.id
            name = body.get('name', '')
            method = body.get('method')
            url = body.get('url', "")
            header = body.get('headers', {})
            times = body.get("times", "1")
            json_data = body.get("json", {})
            form = {
                "data": body.get('form', {}),
                "desc": desc.get('form', {})
            }
            params = {
                "params": body.get('params', {}),
                "desc": desc.get('params', {})
            }
            files = {
                "files": body.get('files', {}),
                "desc": desc.get('files', {})
            }
            extract = {
                "extract": body.get('extract', []),
                "desc": desc.get('extract', {})
            }
            validate = {
                "validate": body.get('validate', []),
            }
            variables = {
                "variables": body.get('variables', []),
            }
            setup_hooks = body.get('setup_hooks', [])
            teardown_hooks = body.get('teardown_hooks', [])
            data.append({
                'id': id,
                'name': name,
                'method': method,
                'url': url,
                'header': json.dumps(header, ensure_ascii=False),
                'times': times,
                'json': json.dumps(json_data, ensure_ascii=False),
                'form': json.dumps(form, ensure_ascii=False),
                'params': json.dumps(params, ensure_ascii=False),
                'files': json.dumps(files, ensure_ascii=False),
                'extract': json.dumps(extract, ensure_ascii=False),
                'validate': json.dumps(validate, ensure_ascii=False),
                'variables': json.dumps(variables, ensure_ascii=False),
                'setup_hooks': json.dumps(setup_hooks, ensure_ascii=False),
                'teardown_hooks': json.dumps(teardown_hooks, ensure_ascii=False),
            })
        sio = export_apis(data)
        now = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = u"{date}_{project_id}_{relation}.xls".format(
            project_id=project_id,
            relation=relation,
            date=now
        )
        response = HttpResponse(sio.getvalue(), content_type='application/vnd.ms-excel')
        response['Content-Disposition'] = 'attachment; filename={}'.format(filename)
        response.write(sio.getvalue())
        return response
