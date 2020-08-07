from datetime import datetime

from django.db import models

from users.models import UserProfile


# 定义项目
class Server(models.Model):
    zctype = models.ForeignKey('servers.ServerType', on_delete=models.CASCADE)
    ipaddress = models.CharField(max_length=100, verbose_name='项目名', blank=True)
    description = models.CharField(max_length=50, verbose_name='项目概述', blank=True)
    brand = models.CharField(max_length=50, verbose_name='开发令号', blank=True)
    zcmodel = models.CharField(max_length=50, verbose_name='开始时间', blank=True)
    zcnumber = models.CharField(max_length=50, verbose_name='完成时间', blank=True)
    zcpz = models.CharField(max_length=100, verbose_name='项目现状', blank=True)
    owner = models.ForeignKey('users.UserProfile', on_delete=models.SET_NULL, null=True, blank=True)
    undernet = models.CharField(max_length=10, verbose_name='延期风险')
    guartime = models.CharField(max_length=50, verbose_name='项目级别', blank=True)
    comment = models.CharField(max_length=300, verbose_name='备注', blank=True)
    warn_times = models.IntegerField(verbose_name='项目预警次数', default=0)
    modify_time = models.DateTimeField(default=datetime.now, verbose_name='修改时间')

    class Meta:
        verbose_name = '项目信息表'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.undernet


# 定义项目类型model
class ServerType(models.Model):
    zctype = models.CharField(max_length=20, verbose_name='项目类型')

    class Meta:
        verbose_name = '项目类型表'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.zctype


# 项目历史信息表
class ServerHis(models.Model):
    serverid = models.IntegerField(verbose_name='序号')
    zctype = models.CharField(max_length=20, verbose_name='项目类型')
    ipaddress = models.CharField(max_length=100, verbose_name='项目名', blank=True)
    description = models.CharField(max_length=50, verbose_name='项目概述', blank=True)
    brand = models.CharField(max_length=50, verbose_name='开发令号', blank=True)
    zcmodel = models.CharField(max_length=50, verbose_name='开始时间', blank=True)
    zcnumber = models.CharField(max_length=50, verbose_name='完成时间', blank=True)
    zcpz = models.CharField(max_length=100, verbose_name='项目现状', blank=True)
    owner = models.CharField(max_length=20, verbose_name='负责人')
    undernet = models.CharField(max_length=10, verbose_name='延期风险')
    guartime = models.CharField(max_length=10, verbose_name='项目等级', blank=True)
    comment = models.CharField(max_length=300, verbose_name='备注', blank=True)
    modify_time = models.DateTimeField(default=datetime.now, verbose_name='修改时间')

    class Meta:
        verbose_name = '项目历史表'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.zctype
