#!/usr/bin/env python
# -*- encoding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from django.contrib import admin
from django.contrib.admin.models import LogEntry

from fastrunner.models import *

admin.site.site_header = 'FasterRunner后台管理'
admin.site.site_title = 'FasterRunner后台管理'


# @admin.register(LogEntry)
class CommonSettingAdmin(admin.ModelAdmin):
    list_per_page = 20
    ordering= ['id']

class ProjectAdmin(CommonSettingAdmin):
    list_display = [obj.name for obj in Project._meta.fields]


class ConfigAdmin(CommonSettingAdmin):
    list_display = [obj.name for obj in Config._meta.fields]
    search_fields = ['name', 'body']
    list_filter = ['project']


class APIAdmin(CommonSettingAdmin):
    list_display = [obj.name for obj in API._meta.fields]
    search_fields = ['name']
    list_filter = ['relation']


class CaseAdmin(CommonSettingAdmin):
    list_display = [obj.name for obj in Case._meta.fields]


class CaseStepAdmin(CommonSettingAdmin):
    list_display = [obj.name for obj in CaseStep._meta.fields]


class HostIPAdmin(CommonSettingAdmin):
    list_display = [obj.name for obj in HostIP._meta.fields]


class VariablesAdmin(CommonSettingAdmin):
    list_display = [obj.name for obj in Variables._meta.fields]


class ReportAdmin(CommonSettingAdmin):
    list_display = [obj.name for obj in Report._meta.fields]


class ReportDetailAdmin(CommonSettingAdmin):
    list_display = [obj.name for obj in ReportDetail._meta.fields]


class RelationAdmin(CommonSettingAdmin):
    list_display = [obj.name for obj in Relation._meta.fields]


class ModelWithFileFieldAdmin(CommonSettingAdmin):
    list_display = [obj.name for obj in ModelWithFileField._meta.fields]


class APITemplateFileAdmin(CommonSettingAdmin):
    list_display = [obj.name for obj in APITemplateFile._meta.fields]


class LockFilesAdmin(CommonSettingAdmin):
    list_display = [obj.name for obj in LockFiles._meta.fields]


class LockFilesAdmin(CommonSettingAdmin):
    list_display = [obj.name for obj in LockFiles._meta.fields]


class PycodeAdmin(CommonSettingAdmin):
    list_display = [obj.name for obj in Pycode._meta.fields]


class HelperAdmin(CommonSettingAdmin):
    list_display = [obj.name for obj in Helper._meta.fields]


@admin.register(LogEntry)
class LogEntryAdmin(admin.ModelAdmin):
    list_per_page = 20
    list_display = ['object_repr', 'action_flag', 'user', 'change_message', 'action_time']


admin.site.register(Project, ProjectAdmin)
admin.site.register(Config, ConfigAdmin)
admin.site.register(API, APIAdmin)
admin.site.register(Case, CaseAdmin)
admin.site.register(CaseStep, CaseStepAdmin)
admin.site.register(HostIP, HostIPAdmin)
admin.site.register(Variables, VariablesAdmin)
admin.site.register(Report, ReportAdmin)
admin.site.register(ReportDetail, ReportDetailAdmin)
admin.site.register(Relation, RelationAdmin)
admin.site.register(ModelWithFileField, ModelWithFileFieldAdmin)
admin.site.register(APITemplateFile, APITemplateFileAdmin)
admin.site.register(LockFiles, LockFilesAdmin)
admin.site.register(Pycode, PycodeAdmin)
admin.site.register(Helper, HelperAdmin)
