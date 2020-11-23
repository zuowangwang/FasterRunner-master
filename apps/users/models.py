# _*_ coding: utf-8 _*_
from django.db import models
from django.contrib.auth.models import AbstractUser
from fastrunner.models import Project


class User(AbstractUser):
    belong_project = models.ManyToManyField(Project, blank=True, help_text="所属项目", verbose_name="所属项目",
                                            related_name="user_set", related_query_name="user")

    class Meta:
        verbose_name = "用户信息"
        verbose_name_plural = verbose_name
        db_table = 'auth_user'

    def __str__(self):
        return self.username
