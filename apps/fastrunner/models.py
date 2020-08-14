from django.db import models


class BaseTable(models.Model):
    """
    公共字段列
    """

    class Meta:
        abstract = True
        verbose_name = "公共字段表"
        db_table = 'BaseTable'

    create_time = models.DateTimeField('创建时间', auto_now_add=True)
    update_time = models.DateTimeField('更新时间', auto_now=True)


class Project(BaseTable):
    """
    项目信息表
    """

    class Meta:
        verbose_name = "项目信息"
        verbose_name_plural = verbose_name

    name = models.CharField("项目名称", unique=True, null=False, max_length=100)
    desc = models.CharField("简要介绍", max_length=100, null=False)
    responsible = models.CharField("负责人", max_length=20, null=False)

    def __str__(self):
        return self.name


class Config(BaseTable):
    """
    环境信息表
    """

    class Meta:
        verbose_name = "配置信息"
        verbose_name_plural = verbose_name
        unique_together = [['project', 'name']]

    name = models.CharField("环境名称", null=False, max_length=100)
    body = models.TextField("主体信息", null=False)
    base_url = models.CharField("请求地址", null=True, blank=True, max_length=100)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)

    def __str__(self):
        return self.name


class API(BaseTable):
    """
    API信息表
    """

    class Meta:
        verbose_name = "接口信息"
        verbose_name_plural = verbose_name

    name = models.CharField("接口名称", null=False, max_length=100)
    body = models.TextField("主体信息", null=False)
    url = models.CharField("请求地址", null=False, max_length=200)
    method = models.CharField("请求方式", null=False, max_length=10)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    relation = models.IntegerField("节点id", null=False)

    def __str__(self):
        return self.name


class Case(BaseTable):
    """
    用例信息表
    """

    class Meta:
        verbose_name = "用例信息"
        verbose_name_plural = verbose_name

    tag = (
        (1, "冒烟用例"),
        (2, "集成用例"),
        (3, "监控脚本")
    )
    name = models.CharField("用例名称", null=False, max_length=500)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, help_text="所属项目")
    relation = models.IntegerField("节点id", null=False)
    length = models.IntegerField("API个数", null=False)
    tag = models.IntegerField("用例标签", choices=tag, default=2)

    def __str__(self):
        return self.name


class CaseStep(BaseTable):
    """
    Test Case Step
    """

    class Meta:
        verbose_name = "用例信息 Step"
        verbose_name_plural = verbose_name

    name = models.CharField("api名称", null=False, max_length=100)
    body = models.TextField("主体信息", null=False)
    url = models.CharField("请求地址", null=False, max_length=300)
    method = models.CharField("请求方式", null=False, max_length=10)
    case = models.ForeignKey(Case, on_delete=models.CASCADE, help_text="所属case")
    step = models.IntegerField("api顺序", null=False)
    apiId = models.IntegerField('所属api_id', null=False, default=0)

    def __str__(self):
        return self.name


class HostIP(BaseTable):
    """
    环境域名
    """

    class Meta:
        verbose_name = "HOST配置"
        verbose_name_plural = verbose_name
        unique_together = [['project', 'name']]

    name = models.CharField(null=False, max_length=20, help_text="环境名称")
    hostInfo = models.TextField(null=False, help_text="环境信息详情")
    project = models.ForeignKey(Project, on_delete=models.CASCADE, help_text="所属项目")
    base_url = models.URLField(null=True, blank=True, help_text="环境根地址")
    # desc = models.CharField(null=True, blank=True, help_text="描述信息", max_length=100, default="")

    def __str__(self):
        return self.name


class Variables(BaseTable):
    """
    全局变量
    """

    class Meta:
        verbose_name = "全局变量"
        verbose_name_plural = verbose_name

    key = models.CharField(null=False, max_length=100)
    value = models.CharField(null=False, max_length=1024)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)

    def __str__(self):
        return self.key


class Report(BaseTable):
    """
    报告存储
    """
    report_type = (
        (1, "调试"),
        (2, "异步"),
        (3, "定时")
    )

    class Meta:
        verbose_name = "测试报告"
        verbose_name_plural = verbose_name

    name = models.CharField("报告名称", null=False, max_length=100)
    type = models.IntegerField("报告类型", choices=report_type)
    summary = models.TextField("简要主体信息", null=False)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)

    def __str__(self):
        return self.name


class ReportDetail(BaseTable):
    """
    报告主题信息存储
    """

    class Meta:
        verbose_name = "测试报告详情"
        verbose_name_plural = verbose_name

    name = models.CharField("报告名称", null=False, max_length=100)
    summary = models.TextField("主体信息", null=False)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    report = models.OneToOneField(Report, on_delete=models.CASCADE)

    def __str__(self):
        return self.name


class Relation(models.Model):
    """
    树形结构关系
    """

    class Meta:
        verbose_name = "树形结构关系"
        verbose_name_plural = verbose_name

    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    tree = models.TextField("结构主题", null=False, default=[])
    type = models.IntegerField("树类型", default=1)


class ModelWithFileField(BaseTable):
    """
    文件信息表
    """
    class Meta:
        verbose_name = "文件信息表"
        verbose_name_plural = verbose_name
        unique_together = [['project', 'name']]

    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    name = models.CharField(max_length=50)
    file = models.FileField(upload_to='testdatas', unique=True, null=True, blank=True)
    relation = models.IntegerField("节点id", null=False, default=1)
    excel_tree = models.TextField("excel的级联数据", null=True, blank=True)

    def __str__(self):
        return self.name


class LockFiles(BaseTable):
    """
    锁定的文件信息表
    """
    class Meta:
        verbose_name = "锁定文件信息表"
        verbose_name_plural = verbose_name
        unique_together = [['project', 'lock_type', 'file_id']]
        default_permissions = ('add',)
    tag = (
        (1, "测试数据"),
    )
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    lock_type = models.CharField(choices=tag, max_length=2, verbose_name="锁定哪个信息表")
    file_id = models.IntegerField(verbose_name="锁定文件的id")

    def __str__(self):
        return 'table:%s - id:%s' % (self.lock_type, self.file_id)


class Pycode(BaseTable):
    """
    驱动文件表
    """

    class Meta:
        verbose_name = "驱动文件库"
        verbose_name_plural = verbose_name
        unique_together = [['project', 'name']]

    code = models.TextField("python代码", default="# _*_ coding:utf-8 _*_", null=False)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    name = models.CharField(max_length=30, null=False)
    desc = models.CharField("简要介绍", max_length=100, null=True, blank=True)

    def __str__(self):
        return self.name
