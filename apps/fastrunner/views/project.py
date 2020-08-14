import os
import xlrd
from xlrd.biffh import XLRDError

from django.core.exceptions import ObjectDoesNotExist
from django.utils.decorators import method_decorator
from rest_framework.viewsets import GenericViewSet, ModelViewSet
from rest_framework import mixins
from rest_framework import status
from rest_framework import exceptions
from rest_framework.response import Response
from rest_framework.permissions import DjangoModelPermissions
from djcelery import models as celery_models
from django.contrib.auth import get_user_model

from fastrunner import models, serializers
from FasterRunner import pagination
from fastrunner.utils import response
from fastrunner.utils import prepare
from fastrunner.utils.decorator import request_log
from fastrunner.utils.runner import DebugCode
from fastrunner.utils.tree import get_tree_max_id
from fastrunner.utils.permissions import IsBelongToProject, _check_is_locked
from FasterRunner.settings import MEDIA_ROOT

UserModel = get_user_model()


class ProjectView(ModelViewSet):
    """
    项目增删改查
    """
    serializer_class = serializers.ProjectSerializer
    pagination_class = pagination.MyCursorPagination
    permission_classes = (DjangoModelPermissions, IsBelongToProject)

    def get_queryset(self):
        if self.request.user.is_superuser:
            return models.Project.objects.all().order_by('-create_time')
        project_id_list = UserModel.objects.filter(id=self.request.user.id).values_list('belong_project', flat=True)
        return models.Project.objects.filter(id__in=[_ for _ in project_id_list]).order_by('-update_time')

    @method_decorator(request_log(level='INFO'))
    def single(self, request, **kwargs):
        """
        得到单个项目相关统计信息
        """
        pk = kwargs.pop('pk')

        try:
            queryset = models.Project.objects.get(id=pk)
        except ObjectDoesNotExist:
            return Response(response.PROJECT_NOT_EXISTS)

        serializer = self.get_serializer(queryset, many=False)

        project_info = prepare.get_project_detail(pk)
        project_info.update(serializer.data)

        return Response(project_info)

    def perform_create(self, serializer):
        instance = serializer.save()
        # 生成debugtalk.py文件
        models.Pycode.objects.create(project=instance, name="debugtalk.py", desc="项目的根目录文件，项目中所使用函数都从此中调用")
        models.Pycode.objects.create(project=instance, name="get_excel_data.py", desc="获取excel表格数据", code="""
# _*_ coding:utf-8 _*_
import xlrd
import os

class Xlaccountinfo():
    # 获取excel数据，从第三行开始，第二行是表头，第一行是备注
    def __init__(self, path=''):
        self.xl = xlrd.open_workbook(path)

    def floattostr(self, val):
        if isinstance(val, float) and float(int(val)) != val:
            val = str(int(val))
        if val.lower() == 'true':
            val = True
        elif val.lower() == 'false':
            val = False
        return val

    def get_sheetinfo_by_name(self, name):
        self.sheet = self.xl.sheet_by_name(name)
        return self.get_sheet_info()

    def get_sheetinfo_by_index(self, index):
        self.sheet = self.xl.sheet_by_index(index)
        return self.get_sheet_info()

    def get_sheetinfo_by_rowName(self, name):
        self.sheet = self.xl.sheet_by_name(name)
        infolist = []
        for col in range(self.sheet.ncols):
            if col == 0:
                listKey = [self.floattostr(val.strip()) for val in self.sheet.col_values(col)]
            elif col == 1:
                info = [self.floattostr(val.strip()) for val in self.sheet.col_values(col)]
                tmp = zip(listKey, info)
                infolist.append(dict(tmp))
        return infolist

    def get_sheet_info(self):
        infolist = []
        for row in range(1, self.sheet.nrows):
            if row == 1:
                listKey = [self.floattostr(val.strip()) for val in self.sheet.row_values(row)]
            else:
                info = [self.floattostr(val.strip()) for val in self.sheet.row_values(row)]
                tmp = zip(listKey, info)
                infolist.append(dict(tmp))
        return infolist


# 通过行获取excel数据
def get_xlsx_by_cols(excelName, sheetName):
    xlinfo = Xlaccountinfo(excelName)
    info = xlinfo.get_sheetinfo_by_name(sheetName)
    return info

# 通过列获取excel数据
def xlsxPlatform(excelName, sheetName):
    xlinfo = Xlaccountinfo(excelName)
    info = xlinfo.get_sheetinfo_by_rowName(sheetName)
    return info
    
if __name__ == '__main__':
    excelName = os.environ["excelName"]
    sheetName = os.environ["excelsheet"]
                                     """)
        # 自动生成API tree
        models.Relation.objects.create(project=instance)
        # 自动生成Test Tree
        models.Relation.objects.create(project=instance, type=2)
        # 自动生成 TestData Tree
        models.Relation.objects.create(project=instance, type=3)

    def perform_destroy(self, instance):
        project_id = instance.id
        celery_models.PeriodicTask.objects.filter(description=project_id).delete()
        instance.delete()


class DashboardView(GenericViewSet):
    """
    dashboard信息
    """
    # permission_classes = (DjangoModelPermissions, IsBelongToProject)
    @method_decorator(request_log(level='INFO'))
    def get(self, request, **kwargs):
        return Response(prepare.get_project_detail(kwargs['pk']))


class TreeView(GenericViewSet):
    """
    树形结构操作
    """
    permission_classes = (DjangoModelPermissions, IsBelongToProject)

    def get_queryset(self):
        project_id = self.kwargs.get('pk')
        queryset = models.Relation.objects.filter(project__id=project_id).order_by('-update_time')
        return queryset

    @method_decorator(request_log(level='INFO'))
    def get(self, request, **kwargs):
        """
        返回树形结构
        当前最带节点ID
        """

        try:
            tree_type = request.query_params['type']
        except KeyError:
            return Response(response.KEY_MISS)
        try:
            tree = models.Relation.objects.get(project_id=kwargs['pk'], type=tree_type)
            body = eval(tree.tree)
        except ObjectDoesNotExist as e:
            tree = models.Relation.objects.create(project_id=kwargs['pk'], type=tree_type, tree=[{'id': 1, 'label': 'testdata', 'children': []}])
            body = []

        tree = {
            "tree": body,
            "id": tree.id,
            "success": True,
            "max": get_tree_max_id(body)
        }
        return Response(tree)

    @method_decorator(request_log(level='INFO'))
    def patch(self, request, **kwargs):
        """
        修改树形结构，ID不能重复
        """
        try:
            body = request.data['body']
            mode = request.data['mode']

            relation = models.Relation.objects.get(id=kwargs['pk'])
            relation.tree = body
            relation.save()

        except KeyError:
            return Response(response.KEY_MISS)

        except ObjectDoesNotExist:
            return Response(response.SYSTEM_ERROR)

        #  mode -> True remove node
        if mode:
            prepare.tree_end(request.data, relation.project)

        response.TREE_UPDATE_SUCCESS['tree'] = body
        response.TREE_UPDATE_SUCCESS['max'] = get_tree_max_id(body)

        return Response(response.TREE_UPDATE_SUCCESS)


class FileView(GenericViewSet, mixins.CreateModelMixin, mixins.ListModelMixin, mixins.DestroyModelMixin):
    """
    list:当前项目文件列表
    create:上传与更新文件
    destroy:删除文件
    """
    serializer_class = serializers.FileSerializer
    pagination_class = pagination.MyPageNumberPagination
    permission_classes = (DjangoModelPermissions, IsBelongToProject)

    def get_queryset(self):
        if self.action == 'create':
            project = self.request.data['project']
            name = self.request.data['name']
            return models.ModelWithFileField.objects.filter(project__id=project, name=name).order_by('-update_time')
        else:
            project = self.request.query_params['project']
            queryset = models.ModelWithFileField.objects.filter(project__id=project).order_by('-update_time')
            if self.action == 'list':
                node = self.request.query_params.get('node', '')
                search = self.request.query_params.get('search', '')
                if search != '':
                    queryset = queryset.filter(name__contains=search)
                if node != '':
                    queryset = queryset.filter(relation=node)
            return queryset

    def create(self, request, *args, **kwargs):
        if not self.get_queryset():
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
        else:
            self.kwargs['pk'] = self.get_queryset()[0].id
            _check_is_locked(request.data['project'], 1, self.kwargs['pk'])

            instance = self.get_object()
            filepath = os.path.join(MEDIA_ROOT, str(instance.file))
            if os.path.exists(filepath):
                os.remove(filepath)
            req_relation = request.data.get("relation", '')
            if not req_relation:
                request.data["relation"] = instance.relation

            partial = kwargs.pop('partial', False)
            serializer = self.get_serializer(instance, data=request.data, partial=partial)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            if getattr(instance, '_prefetched_objects_cache', None):
                # If 'prefetch_related' has been applied to a queryset, we need to
                # forcibly invalidate the prefetch cache on the instance.
                instance._prefetched_objects_cache = {}

            return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        if kwargs.get('pk') and int(kwargs['pk']) != -1:
            _check_is_locked(request.query_params['project'], 1, kwargs['pk'])
            instance = self.get_object()
            filepath = os.path.join(MEDIA_ROOT, str(instance.file))
            if os.path.exists(filepath):
                os.remove(filepath)
            self.perform_destroy(instance)
        elif request.data:
            for content in request.data:
                self.kwargs['pk'] = content['id']
                try:
                    _check_is_locked(content['project'], 1, content['id'])
                except exceptions.NotAcceptable as e:
                    continue
                instance = self.get_object()
                filepath = os.path.join(MEDIA_ROOT, str(instance.file))
                if os.path.exists(filepath):
                    os.remove(filepath)
                self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def perform_create(self, serializer):
        serializer.save()
        try:
            excel_file = models.ModelWithFileField.objects.get(id=serializer.data["id"])
            file_path = os.path.join(MEDIA_ROOT, str(excel_file.file))
            excel_info = xlrd.open_workbook(file_path)
            excel_tree = {"value": excel_file.name, "label": excel_file.name, "children": []}
            for sheet in excel_info.sheets():
                excel_tree["children"].append({"value": sheet.name, "label": sheet.name})
            excel_file.excel_tree = excel_tree
            excel_file.save()
        except XLRDError as e:
            pass


class PycodeRunView(GenericViewSet, mixins.RetrieveModelMixin):
    """
    驱动代码调试运行
    """
    serializer_class = serializers.PycodeSerializer
    permission_classes = (DjangoModelPermissions, IsBelongToProject)

    def get_queryset(self):
        project = self.request.query_params["project"]
        queryset = models.Pycode.objects.filter(project_id=project).order_by('-update_time')
        return queryset

    @method_decorator(request_log(level='INFO'))
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)

        debug = DebugCode(serializer.data["code"], serializer.data["project"], serializer.data["name"])
        debug.run()

        debug_rsp = {
            "msg": debug.resp
        }
        return Response(data=debug_rsp)


class PycodeView(ModelViewSet):
    """
    驱动代码模块
    """
    serializer_class = serializers.PycodeSerializer
    pagination_class = pagination.MyPageNumberPagination
    permission_classes = (DjangoModelPermissions, IsBelongToProject)

    def get_queryset(self):
        project = self.request.query_params["project"]
        queryset = models.Pycode.objects.filter(project_id=project).order_by('-update_time')
        if self.action == 'list':
            queryset = queryset.filter(name__contains=self.request.query_params["search"])
        return queryset

    @method_decorator(request_log(level='INFO'))
    def destroy(self, request, *args, **kwargs):
        if kwargs.get('pk') and int(kwargs['pk']) != -1:
            instance = self.get_object()
            if instance.name == 'debugtalk.py':
                Response(status=status.HTTP_423_LOCKED)
            else:
                self.perform_destroy(instance)
        elif request.data:
            for content in request.data:
                self.kwargs['pk'] = content['id']
                instance = self.get_object()
                if instance.name != 'debugtalk.py':
                    self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)
