import csv
import time
from django.shortcuts import render
from django.views.generic.base import View
from django.http.response import HttpResponseRedirect, HttpResponse, JsonResponse
from django.urls import reverse
from django.db.models import Q, Count
from pure_pagination import Paginator, PageNotAnInteger
from .models import Server, ServerType, ServerHis
from .forms import ServerForm, ServerTypeForm
from users.models import UserOperateLog, UserProfile
from zcgl.settings import per_page
from utils.mixin_utils import LoginRequiredMixin
from django.conf import settings
from django.core import mail


# 定义首页视图
class IndexView(LoginRequiredMixin, View):
    def get(self, request):
        total = Server.objects.count()
        zctype_groups = Server.objects.values("zctype__zctype").annotate(zctype_num=Count("zctype")).all(). \
            order_by('-zctype_num', 'zctype__zctype')
        return render(request, 'servers/index.html', {'zctype_groups': zctype_groups, 'total': total})


# 项目列表
class ServerListView(LoginRequiredMixin, View):
    def get(self, request):
        self.auto_warning()  # 自动预警功能
        search = request.GET.get('search')
        if search:
            search = request.GET.get('search').strip()
            # 如果输入的是纯数字，则将序号也加入到搜索的列表中来
            try:
                search_int = int(search)
                servers = Server.objects.filter(Q(id=search_int) | Q(zctype__zctype__icontains=search)
                                                | Q(ipaddress__icontains=search) | Q(description__icontains=search)
                                                | Q(brand__icontains=search) | Q(zcmodel__icontains=search)
                                                | Q(zcnumber__icontains=search) | Q(comment__icontains=search)
                                                | Q(zcpz__icontains=search) | Q(owner__username__icontains=search)). \
                    order_by('zctype', 'id')
            except Exception:
                servers = Server.objects.filter(Q(zctype__zctype__icontains=search)
                                                | Q(ipaddress__icontains=search) | Q(description__icontains=search)
                                                | Q(brand__icontains=search) | Q(zcmodel__icontains=search)
                                                | Q(zcnumber__icontains=search) | Q(comment__icontains=search)
                                                | Q(zcpz__icontains=search) | Q(owner__username__icontains=search)). \
                    order_by('zctype', 'id')
        else:
            servers = Server.objects.all().order_by('id', 'zctype')

        # 分页功能实现
        try:
            page = request.GET.get('page', 1)
        except PageNotAnInteger:
            page = 1
        p = Paginator(servers, per_page=per_page, request=request)
        p_servers = p.page(page)
        start = (int(page) - 1) * per_page  # 避免分页后每行数据序号从1开始
        return render(request, 'servers/server_list.html', {'p_servers': p_servers, 'start': start, 'search': search})

    def auto_warning(self):
        '''
        自动预警功能,当完成时间已经超过当前时间时,项目变为有风险
        '''
        projects = Server.objects.all()
        for project in projects:
            end_time = time.strptime(project.zcnumber, '%Y-%m-%d')
            end_time = time.mktime(end_time)
            now_time = time.time()
            if end_time - now_time < 0:
                project.undernet = '1'
                project.save()


# 项目添加
class ServerAddView(LoginRequiredMixin, View):
    def get(self, request):
        users = UserProfile.objects.filter(is_superuser=0, is_staff='1')
        server_types = ServerType.objects.all()
        return render(request, 'servers/server_add.html', {'users': users, 'server_types': server_types})

    def post(self, request):
        zctype = ServerType.objects.filter(id=request.POST.get('zctype', 0)).first()
        ipaddress = request.POST.get('ipaddress').strip().upper()
        description = request.POST.get('description').strip().upper()
        brand = request.POST.get('brand').strip().upper()
        zcmodel = request.POST.get('zcmodel')
        zcnumber = request.POST.get('zcnumber')
        zcpz = request.POST.get('zcpz').strip().upper()
        owner = UserProfile.objects.filter(id=request.POST.get('owner', 0)).first()
        undernet = request.POST.get('undernet')
        guartime = request.POST.get('guartime').strip().upper()
        comment = request.POST.get('comment').strip().upper()

        server_form = ServerForm(request.POST)
        # 判断表单是否正确
        if server_form.is_valid():
            new_server = Server(zctype=zctype, ipaddress=ipaddress, description=description, brand=brand,
                                zcmodel=zcmodel, zcnumber=zcnumber, zcpz=zcpz, owner=owner, undernet=undernet,
                                guartime=guartime, comment=comment)
            new_server.save()

            user_name = owner.username if owner else ''

            # 该记录添加到历史表中
            server_his = ServerHis(serverid=new_server.id, zctype=zctype.zctype, ipaddress=ipaddress,
                                   description=description, brand=brand, zcmodel=zcmodel, zcnumber=zcnumber,
                                   zcpz=zcpz, owner=user_name, undernet=undernet, guartime=guartime, comment=comment)
            server_his.save()

            # 将操作记录添加到日志中
            new_log = UserOperateLog(username=request.user.username, scope=zctype.zctype, type='增加',
                                     content=server_his.serverid)
            new_log.save()
            return HttpResponseRedirect((reverse('servers:server_list')))
        else:
            users = UserProfile.objects.filter(is_superuser=0)
            server_types = ServerType.objects.all()
            return render(request, 'servers/server_add.html', {'msg': '输入错误！', 'users': users,
                                                               'server_form': server_form,
                                                               'server_types': server_types})


# 项目详情
class ServerDetailView(LoginRequiredMixin, View):
    def get(self, request, server_id):
        server = Server.objects.filter(id=server_id).first()
        users = UserProfile.objects.filter(is_superuser=0, is_staff='1')
        server_types = ServerType.objects.all()
        server_hiss = ServerHis.objects.filter(serverid=server_id).order_by('-modify_time')

        # 分页功能实现
        try:
            page = request.GET.get('page', 1)
        except PageNotAnInteger:
            page = 1
        p = Paginator(server_hiss, per_page=per_page, request=request)
        p_server_hiss = p.page(page)
        start = (int(page) - 1) * per_page  # 避免分页后每行数据序号从1开始
        return render(request, 'servers/server_detail.html', {'users': users, 'server': server,
                                                              'server_types': server_types,
                                                              'p_server_hiss': p_server_hiss, 'start': start})


# 项目修改
class ServerModifyView(LoginRequiredMixin, View):
    def post(self, request):
        server_id = int(request.POST.get('server_id'))
        server = Server.objects.filter(id=server_id).first()
        server_form = ServerForm(request.POST)
        # 判断表单是否正确
        if server_form.is_valid():
            server.zctype = ServerType.objects.filter(id=request.POST.get('zctype')).first()
            server.ipaddress = request.POST.get('ipaddress').strip().upper()
            server.description = request.POST.get('description').strip().upper()
            server.brand = request.POST.get('brand').strip().upper()
            server.zcmodel = request.POST.get('zcmodel')
            server.zcnumber = request.POST.get('zcnumber')
            server.zcpz = request.POST.get('zcpz').strip().upper()
            server.owner = UserProfile.objects.filter(id=request.POST.get('owner', 0)).first()
            server.undernet = request.POST.get('undernet')
            server.guartime = request.POST.get('guartime').strip().upper()
            server.comment = request.POST.get('comment').strip().upper()
            server.save()

            user_name = server.owner.username if server.owner else ''

            # 该记录添加到历史表中
            server_his = ServerHis(serverid=server.id, zctype=server.zctype.zctype, ipaddress=server.ipaddress,
                                   description=server.description, brand=server.brand, zcmodel=server.zcmodel,
                                   zcnumber=server.zcnumber, zcpz=server.zcpz, owner=user_name,
                                   undernet=server.undernet, guartime=server.guartime, comment=server.comment)
            server_his.save()

            # 将操作记录添加到日志中
            new_log = UserOperateLog(username=request.user.username, scope=server.zctype, type='修改',
                                     content=server_id)
            new_log.save()
            return HttpResponseRedirect((reverse('servers:server_list')))
        else:
            users = UserProfile.objects.filter(is_superuser=0, is_staff='1')
            server_types = ServerType.objects.all()
            return render(request, 'servers/server_detail.html', {'users': users, 'server': server,
                                                                  'server_types': server_types,
                                                                  'msg': '输入错误！', 'server_form': server_form})


# 项目删除
class ServerDeleteView(LoginRequiredMixin, View):
    def get(self, request, server_id):
        server = Server.objects.get(id=server_id)
        scope = server.zctype
        user_name = server.owner.username if server.owner else ''

        # 该记录添加到历史表中
        server_his = ServerHis(serverid=server.id, zctype=server.zctype.zctype, ipaddress=server.ipaddress,
                               description=server.description, brand=server.brand, zcmodel=server.zcmodel,
                               zcnumber=server.zcnumber, zcpz=server.zcpz, owner=user_name,
                               undernet=server.undernet, guartime=server.guartime, comment='该记录被删除')
        server_his.save()

        # 删除该记录
        server.delete()

        # 将操作记录添加到日志中
        new_log = UserOperateLog(username=request.user.username, scope=scope, type='删除',
                                 content=str(server_id))
        new_log.save()
        return HttpResponseRedirect((reverse('servers:server_list')))


# 项目列表导出
class ServerExportView(LoginRequiredMixin, View):
    def get(self, request):
        search = request.GET.get('search')
        if search:
            search = request.GET.get('search').strip()
            servers = Server.objects.filter(Q(zctype__zctype__icontains=search) | Q(ipaddress__icontains=search)
                                            | Q(description__icontains=search) | Q(brand__icontains=search)
                                            | Q(zcmodel__icontains=search) | Q(zcnumber__icontains=search)
                                            | Q(zcpz__icontains=search) | Q(owner__username__icontains=search)). \
                order_by('zctype')
        else:
            servers = Server.objects.all().order_by('zctype')
        servers = servers.values('id', 'zctype__zctype', 'ipaddress', 'description', 'brand', 'zcmodel', 'zcnumber',
                                 'zcpz', 'owner__username', 'undernet', 'guartime', 'comment')
        colnames = ['序号', '项目类型', 'IP地址', '功能描述', '设备品牌', '设备型号', '设备序号', '设备配置',
                    '管理人员', '所在网络', '保修期', '备注']
        response = create_excel(colnames, servers, 'project_table')
        return response


def create_excel(columns, content, file_name):
    """创建导出csv的函数"""
    file_name = file_name + '.csv'
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename=' + file_name
    response.charset = 'gbk'
    writer = csv.writer(response)
    writer.writerow(columns)
    for i in content:
        writer.writerow([i['id'], i['zctype__zctype'], i['ipaddress'], i['description'], i['brand'], i['zcmodel'],
                         i['zcnumber'], i['zcpz'], i['owner__username'], i['undernet'], i['guartime'], i['comment']])
    return response


# 项目类型列表
class TypeListView(LoginRequiredMixin, View):
    def get(self, request):
        server_types = ServerType.objects.all()
        return render(request, 'servers/type_list.html', {'server_types': server_types})


# 项目类型添加
class TypeAddView(LoginRequiredMixin, View):
    def get(self, request):
        return render(request, 'servers/type_add.html', {})

    def post(self, request):
        zctype = request.POST.get('zctype').strip().upper()
        servertype_form = ServerTypeForm(request.POST)
        # 判断表单是否正确
        if servertype_form.is_valid():
            other_servertype = ServerType.objects.filter(zctype=zctype)
            # 判断是否已经存在了该zctype
            if other_servertype:
                return render(request, 'servers/type_add.html', {'msg': zctype + ' 已存在！'})
            else:
                new_servertype = ServerType(zctype=zctype)
                new_servertype.save()
                return HttpResponseRedirect((reverse('servers:type_list')))
        else:
            return render(request, 'servers/type_add.html', {'msg': '输入错误！', 'servertype_form': servertype_form})


# 项目类型详情
class TypeDetailView(LoginRequiredMixin, View):
    def get(self, request, type_id):
        server_type = ServerType.objects.get(id=type_id)
        return render(request, 'servers/type_detail.html', {'server_type': server_type})


# 项目类型修改
class TypeModifyView(LoginRequiredMixin, View):
    def post(self, request):
        type_id = int(request.POST.get('type_id'))
        zctype = request.POST.get('zctype').strip().upper()
        exist_server_type = ServerType.objects.get(id=type_id)
        other_server_type = ServerType.objects.filter(~Q(id=type_id), zctype=zctype)
        servertype_form = ServerTypeForm(request.POST)
        # 判断表单是否正确
        if servertype_form.is_valid():
            # 如果修改了项目类型名字，判断是否该名字与其他项目类型名字冲突
            if other_server_type:
                return render(request, 'servers/type_detail.html', {'server_type': exist_server_type,
                                                                    'msg': zctype + ' 已存在！'})
            else:
                exist_server_type.zctype = zctype
                exist_server_type.save()
                return HttpResponseRedirect((reverse('servers:type_list')))
        else:
            return render(request, 'servers/type_detail.html', {'server_type': exist_server_type,
                                                                'msg': '输入错误！',
                                                                'servertype_form': servertype_form})


def send_mail_view(request):
    '''
    发送项目预警邮件
    '''
    server_id = request.GET.get('id')
    try:
        project = Server.objects.get(id=server_id, undernet='1')
        staff = project.owner
        email = staff.email
        message = mail_info(project, staff)
        mail.send_mail(subject='项目延期预警邮件',
                       message=message,
                       from_email='1129212285@qq.com',
                       recipient_list=[email])
        times = project.warn_times + 1
        project.warn_times = times
        project.save()
        return JsonResponse({'code': 200, 'data': message, 'times': times})
    except Exception as e:
        return JsonResponse({'code': '对不起,邮件预警服务有错,请联系后台管理员！'})


def mail_info(project, staff):
    '''
    预警邮件信息内容
    '''
    project_name = project.ipaddress  # 项目名
    end_time = project.zcnumber  # 预计完成时间
    last_time = time.strptime(end_time, '%Y-%m-%d')
    last_time = time.mktime(last_time)
    now_time = time.time()
    sub_time = now_time - last_time
    day = sub_time // (3600 * 24)
    mouth = (sub_time // 3600) - day * 24
    minute = int((sub_time % 3600) / 60)
    delay_time = '{}天{}时{}秒'.format(int(day), int(mouth), minute)  # 延期时间
    staff_no = staff.staff_no  # 工号
    department = staff.department  # 部门
    name = staff.username  # 姓名
    now = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
    result = '亲爱的{}:\n<工号：{},部门：{}>;\n' \
             '你的责任项目：<{}>\n计划完成时间为：{};\n现在时间为：{};\n已延期{}!\n' \
             '请尽快组织你的项目或者及时向所在研发小组提出问题！'.format \
        (name, staff_no, department, project_name, end_time, now, delay_time)
    return result
