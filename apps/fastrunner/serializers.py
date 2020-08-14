import json
import os

from rest_framework import serializers
from djcelery import models as celery_models
import xlrd
from xlrd.biffh import XLRDError

from fastrunner import models
from fastrunner.utils.parser import Parse, parser_variables
from FasterRunner.settings import MEDIA_ROOT


class ProjectSerializer(serializers.ModelSerializer):
    """
    项目信息序列化
    """

    class Meta:
        model = models.Project
        fields = '__all__'


class RelationSerializer(serializers.ModelSerializer):
    """
    树形结构序列化
    """

    class Meta:
        model = models.Relation
        fields = '__all__'


class APISerializer(serializers.ModelSerializer):
    """
    接口信息序列化
    """
    body = serializers.SerializerMethodField()

    class Meta:
        model = models.API
        fields = ['id', 'name', 'url', 'method', 'project', 'relation', 'body']

    def get_body(self, obj):
        parse = Parse(eval(obj.body))
        parse.parse_http()
        return parse.testcase


class CaseSerializer(serializers.ModelSerializer):
    """
    用例信息序列化
    """

    class Meta:
        model = models.Case
        fields = '__all__'


class CaseStepSerializer(serializers.ModelSerializer):
    """
    用例步骤序列化
    """
    body = serializers.SerializerMethodField()

    class Meta:
        model = models.CaseStep
        fields = ['id', 'name', 'url', 'method', 'body', 'case']
        depth = 1

    def get_body(self, obj):
        body = eval(obj.body)
        if "base_url" in body["request"].keys():
            return {
                "name": body["name"],
                "method": "config"
            }
        else:
            parse = Parse(eval(obj.body))
            parse.parse_http()
            return parse.testcase


class ConfigSerializer(serializers.ModelSerializer):
    """
    配置信息序列化
    """
    body = serializers.SerializerMethodField()

    class Meta:
        model = models.Config
        fields = ['id', 'base_url', 'body', 'name', 'update_time']
        depth = 1

    def get_body(self, obj):
        parse = Parse(eval(obj.body), level='config')
        parse.parse_http()
        return parse.testcase


class ReportSerializer(serializers.ModelSerializer):
    """
    报告信息序列化
    """
    type = serializers.CharField(source="get_type_display")
    summary = serializers.SerializerMethodField()

    class Meta:
        model = models.Report
        fields = ["id", "name", "type", "summary"]

    def get_summary(self, obj):
        summary = json.loads(obj.summary)
        return summary


class VariablesSerializer(serializers.ModelSerializer):
    """
    变量信息序列化
    """

    class Meta:
        model = models.Variables
        fields = '__all__'


class HostIPSerializerPost(serializers.ModelSerializer):
    """
    环境配置信息序列化
    """
    hostInfo = serializers.JSONField(required=True, help_text="环境配置参数")

    class Meta:
        model = models.HostIP
        fields = '__all__'

    def validate(self, attrs):
        attrs["hostInfo"] = json.dumps(attrs["hostInfo"])
        return attrs


class HostIPSerializerList(serializers.ModelSerializer):
    """
    环境配置信息序列化
    """
    hostInfo = serializers.SerializerMethodField()

    class Meta:
        model = models.HostIP
        fields = '__all__'

    def get_hostInfo(self, obj):
        temp_hostinfo = json.loads(obj.hostInfo)
        hostinfo = parser_variables(temp_hostinfo["variables"], temp_hostinfo["desc"])
        return hostinfo


class PeriodicTaskSerializer(serializers.ModelSerializer):
    """
    定时任务信列表序列化
    """
    kwargs = serializers.CharField(write_only=True)
    args = serializers.CharField(write_only=True)
    total_run_count = serializers.IntegerField(read_only=True)
    summary_kwargs = serializers.SerializerMethodField()
    summary_args = serializers.SerializerMethodField()

    class Meta:
        model = celery_models.PeriodicTask
        fields = '__all__'

    def get_summary_kwargs(self, obj):
        summary_kwargs = json.loads(obj.kwargs)
        receiver = ""
        mail_cc = ""
        self_error = ""
        sensitive_keys = ""
        for _ in summary_kwargs["receiver"]:
            receiver += _ + ';'
        for _ in summary_kwargs["mail_cc"]:
            mail_cc += _ + ';'
        for _ in summary_kwargs["self_error"]:
            self_error += _ + ';'
        for _ in summary_kwargs.get('sensitive_keys', []):
            sensitive_keys += _ + ';'
        summary_kwargs["receiver"] = receiver
        summary_kwargs["mail_cc"] = mail_cc
        summary_kwargs["self_error"] = self_error
        summary_kwargs["sensitive_keys"] = sensitive_keys
        return summary_kwargs

    def get_summary_args(self, obj):
        summary_args = json.loads(obj.args)
        return summary_args


class CrontabScheduleSerializer(serializers.ModelSerializer):
    """
    crontabschedule序列化
    """
    class Meta:
        model = celery_models.CrontabSchedule
        fields = '__all__'


class FileSerializer(serializers.ModelSerializer):
    """
    文件信息序列化
    """
    file = serializers.FileField(required=True, write_only=True, allow_empty_file=False, use_url='testdatas', label="文件",
                                 help_text="文件", error_messages={"blank": "请上传文件", "required": "请上传文件"})
    excel_tree = serializers.SerializerMethodField(help_text="excel文件结构列表")

    def get_excel_tree(self, obj):
        if obj.excel_tree:
            return eval(obj.excel_tree)
        try:
            file_path = os.path.join(MEDIA_ROOT, str(obj.file))
            excel_info = xlrd.open_workbook(file_path)
            excel_tree = {"value": obj.name, "label": obj.name, "children": []}
            for sheet in excel_info.sheets():
                excel_tree["children"].append({"value": sheet.name, "label": sheet.name})
            return excel_tree
        except XLRDError as e:
            pass

    class Meta:
        model = models.ModelWithFileField
        fields = '__all__'


class PycodeSerializer(serializers.ModelSerializer):
    """
    驱动代码序列化
    """

    class Meta:
        model = models.Pycode
        fields = '__all__'
        # fields = ['id', 'update_time', 'code', 'project', 'desc', 'name']


class TaskMetaSerializer(serializers.ModelSerializer):
    """
    异步任务结果序列化
    """
    class Meta:
        model = celery_models.TaskMeta
        fields = ['task_id', 'id', 'status', 'date_done', 'traceback']


class LockFilesSerializer(serializers.ModelSerializer):
    """
    锁定信息序列化
    """
    class Meta:
        model = models.LockFiles
        fields = "__all__"
