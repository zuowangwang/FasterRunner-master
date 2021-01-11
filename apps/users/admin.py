from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User

class MyUserAdmin(admin.ModelAdmin):

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        """
        Get a form Field for a ManyToManyField.
        """
        # db_field.name 本模型下的字段名称
        if db_field.name in ('groups', 'user_permissions', 'belong_project'):
            # 过滤
            # kwargs["queryset"] = Tag.objects.filter(show_status=True)
            # filter_horizontal 保持横向展示
            from django.contrib.admin import widgets
            kwargs['widget'] = widgets.FilteredSelectMultiple(
                db_field.verbose_name,
                db_field.name in self.filter_vertical
            )
        return super(MyUserAdmin, self).formfield_for_foreignkey(db_field, request, **kwargs)

    filter_horizontal = ('groups', 'user_permissions', 'belong_project',)

admin.site.register(User, MyUserAdmin)
