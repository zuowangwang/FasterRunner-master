from django.utils.decorators import method_decorator
from rest_framework.viewsets import ModelViewSet, GenericViewSet, mixins
from rest_framework import status
from rest_framework.response import Response
from rest_framework.permissions import DjangoModelPermissions

from fastrunner import models, serializers
from FasterRunner import pagination
from fastrunner.utils import prepare
from fastrunner.utils.decorator import request_log
from fastrunner.utils.permissions import IsBelongToProject


class TestCaseView(ModelViewSet):
    """
    create:新增测试用例集
        {
            name: str
            project: int,
            relation: int,
            tag:str
            body: [{
                id: int,
                project: int,
                name: str
            }]
        }
    create: copy{
        id: 36
        name: "d"
        project: 6
        relation: 1
        }
    """
    serializer_class = serializers.CaseSerializer
    pagination_class = pagination.MyPageNumberPagination
    permission_classes = (DjangoModelPermissions, IsBelongToProject)

    def get_queryset(self):
        project = self.request.query_params["project"]
        queryset = models.Case.objects.filter(project__id=project).order_by('-update_time')
        if self.action == 'list':
            node = self.request.query_params["node"]
            search = self.request.query_params["search"]
            if search != '':
                queryset = queryset.filter(name__contains=search)
            if node != '':
                queryset = queryset.filter(relation=node)
        return queryset

    @method_decorator(request_log(level='INFO'))
    def create(self, request, *args, **kwargs):
        if 'id' in request.data.keys():
            pk = request.data['id']
            name = request.data['name']
            case_info = models.Case.objects.get(id=pk)
            request_data = {
                "name": name,
                "relation": case_info.relation,
                "length": case_info.length,
                "tag": case_info.tag,
                "project": case_info.project_id
            }
            serializer = self.get_serializer(data=request_data)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            case_step = models.CaseStep.objects.filter(case__id=pk)
            for step in case_step:
                step.id = None
                step.case_id = serializer.data["id"]
                step.save()
        else:
            body = request.data.pop('body')
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)

            case = models.Case.objects.filter(**request.data).first()
            prepare.generate_casestep(body, case)

        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    @method_decorator(request_log(level='INFO'))
    def update(self, request, *args, **kwargs):
        body = request.data.pop('body')

        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)

        prepare.update_casestep(body, instance)

        self.perform_update(serializer)

        if getattr(instance, '_prefetched_objects_cache', None):
            # If 'prefetch_related' has been applied to a queryset, we need to
            # forcibly invalidate the prefetch cache on the instance.
            instance._prefetched_objects_cache = {}

        return Response(serializer.data)

    @method_decorator(request_log(level='INFO'))
    def destroy(self, request, *args, **kwargs):
        project_id = request.query_params["project"]
        if kwargs.get('pk') and int(kwargs['pk']) != -1:
            instance = self.get_object()
            prepare.case_end(int(kwargs['pk']), project_id)
            self.perform_destroy(instance)
        elif request.data:
            for content in request.data:
                self.kwargs['pk'] = content['id']
                instance = self.get_object()
                prepare.case_end(int(kwargs['pk']), project_id)
                self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @method_decorator(request_log(level='INFO'))
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        queryset = models.CaseStep.objects.filter(case__id=kwargs['pk']).order_by('step')
        casestep_serializer = serializers.CaseStepSerializer(queryset, many=True)
        resp = {
            "case": serializer.data,
            "step": casestep_serializer.data
        }
        return Response(resp)


class TestCaseSynchronize(GenericViewSet, mixins.UpdateModelMixin):
    """
    同步测试用例里的api的基本request以及header信息
    """
    serializer_class = serializers.CaseSerializer
    permission_classes = (DjangoModelPermissions, IsBelongToProject)

    def get_queryset(self):
        project = self.request.query_params["project"]
        queryset = models.Case.objects.filter(project__id=project).order_by('-update_time')
        return queryset

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()

        case_id = instance.id
        case_step = models.CaseStep.objects.filter(case_id=case_id).order_by('step')
        for case in case_step:
            if case.method != 'config':
                api_body = eval(models.API.objects.get(id=case.apiId).body)
                csae_body = eval(case.body)
                csae_body["request"] = api_body["request"]
                csae_body["desc"]["header"] = api_body["desc"]["header"]
                csae_body["desc"]["data"] = api_body["desc"]["data"]
                csae_body["desc"]["files"] = api_body["desc"]["files"]
                csae_body["desc"]["params"] = api_body["desc"]["params"]

                case.url = api_body["request"]["url"]
                case.method = api_body["request"]["method"]
                case.body = csae_body
                case.save()

        case_request_data = {}
        serializer = self.get_serializer(instance, data=case_request_data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        if getattr(instance, '_prefetched_objects_cache', None):
            # If 'prefetch_related' has been applied to a queryset, we need to
            # forcibly invalidate the prefetch cache on the instance.
            instance._prefetched_objects_cache = {}

        return Response(serializer.data)
