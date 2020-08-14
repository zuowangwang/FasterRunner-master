# -*- coding: utf-8 -*-
import xadmin
from xadmin import views

from .models import Project, Config, API, Case, CaseStep, HostIP, Variables, Report, ModelWithFileField, Pycode
from djcelery.models import TaskState, WorkerState, PeriodicTask, IntervalSchedule, CrontabSchedule, TaskMeta


class BaseSetting(object):
    enable_themes = True
    use_bootswatch = True


class GlobalSettings(object):
    site_title = "fastrunner后台管理系统"
    site_footer = "fastrunner"


class ProjectAdmin(object):
    list_display = ['name', 'desc', 'responsible', 'create_time', 'update_time']
    search_fields = ['name', 'desc', 'responsible']
    list_filter = ['name', 'desc', 'responsible', 'create_time', 'update_time']
    ordering = ['-update_time']


class ConfigAdmin(object):
    list_display = ['name', 'body', 'base_url', 'project', 'create_time', 'update_time']
    search_fields = ['name', 'body', 'base_url', 'project__name']
    list_filter = ['name', 'body', 'base_url', 'project', 'create_time', 'update_time']
    ordering = ['-update_time']


class APIAdmin(object):
    list_display = ['name', 'body', 'url', 'method', 'relation', 'project', 'create_time', 'update_time']
    search_fields = ['name', 'body', 'url', 'method', 'relation', 'project__name']
    list_filter = ['name', 'body', 'url', 'method', 'relation', 'project', 'create_time', 'update_time']
    ordering = ['-update_time']


class CaseAdmin(object):
    list_display = ['name', 'length', 'tag', 'relation', 'project', 'create_time', 'update_time']
    search_fields = ['name', 'length', 'tag', 'relation', 'project__name']
    list_filter = ['name', 'length', 'tag', 'relation', 'project', 'create_time', 'update_time']
    ordering = ['-update_time']


class CaseStepAdmin(object):
    list_display = ['name', 'body', 'url', 'method', 'case', 'step', 'apiId', 'create_time', 'update_time']
    search_fields = ['name', 'body', 'url', 'method', 'case__name', 'step', 'apiId']
    list_filter = ['name', 'body', 'url', 'method', 'case', 'step', 'apiId', 'create_time', 'update_time']
    ordering = ['-update_time']


class HostIPAdmin(object):
    list_display = ['name', 'hostInfo', 'base_url', 'project', 'create_time', 'update_time']
    search_fields = ['name', 'hostInfo', 'base_url', 'project__name']
    list_filter = ['name', 'hostInfo', 'base_url', 'project', 'create_time', 'update_time']
    ordering = ['-update_time']


class VariablesAdmin(object):
    list_display = ['key', 'value', 'project', 'create_time', 'update_time']
    search_fields = ['key', 'value', 'project__name']
    list_filter = ['key', 'value', 'project', 'create_time', 'update_time']
    ordering = ['-update_time']


class ReportAdmin(object):
    list_display = ['name', 'type', 'summary', 'project', 'create_time']
    search_fields = ['name', 'type', 'summary', 'project__name']
    list_filter = ['name', 'type', 'summary', 'project', 'create_time']
    ordering = ['-create_time']


class ModelWithFileFieldAdmin(object):
    list_display = ['name', 'file', 'project', 'create_time', 'update_time']
    search_fields = ['name', 'file', 'project__name']
    list_filter = ['name', 'file', 'project', 'create_time', 'update_time']
    ordering = ['-update_time']


class PycodeAdmin(object):
    list_display = ['name', 'code', 'desc', 'project', 'create_time', 'update_time']
    search_fields = ['name', 'code', 'desc', 'project__name']
    list_filter = ['name', 'code', 'desc', 'project', 'create_time', 'update_time']
    ordering = ['-update_time']


# 全局配置
# xadmin.site.register(views.BaseAdminView, BaseSetting) #因为配置域名的关系访问不到远程库，所以不使用多主题功能
xadmin.site.register(views.CommAdminView, GlobalSettings)
# djcelery
xadmin.site.register(IntervalSchedule)  # 存储循环任务设置的时间
xadmin.site.register(CrontabSchedule)  # 存储定时任务设置的时间
xadmin.site.register(PeriodicTask)  # 存储任务
xadmin.site.register(TaskState)  # 存储任务执行状态
xadmin.site.register(WorkerState)  # 存储执行任务的worker
xadmin.site.register(TaskMeta)  # 异步任务回执
# 自己的表
xadmin.site.register(Project, ProjectAdmin)
xadmin.site.register(Config, ConfigAdmin)
xadmin.site.register(API, APIAdmin)
xadmin.site.register(Case, CaseAdmin)
xadmin.site.register(CaseStep, CaseStepAdmin)
xadmin.site.register(HostIP, HostIPAdmin)
xadmin.site.register(Variables, VariablesAdmin)
xadmin.site.register(Report, ReportAdmin)
xadmin.site.register(ModelWithFileField, ModelWithFileFieldAdmin)
xadmin.site.register(Pycode, PycodeAdmin)
