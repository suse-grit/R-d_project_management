from django.urls import path
from .views import *

urlpatterns = [
    # 项目url
    path('server/list/', ServerListView.as_view(), name='server_list'),
    path('server/add/', ServerAddView.as_view(), name='server_add'),
    path('server/detail/<int:server_id>/', ServerDetailView.as_view(), name='server_detail'),
    path('server/modify/', ServerModifyView.as_view(), name='server_modify'),
    path('server/delete/<int:server_id>/', ServerDeleteView.as_view(), name='server_delete'),
    path('server/export/', ServerExportView.as_view(), name='server_export'),
    path('send_mail', send_mail_view),
    # 项目类型url
    path('type/list/', TypeListView.as_view(), name='type_list'),
    path('type/add/', TypeAddView.as_view(), name='type_add'),
    path('type/detail/<int:type_id>/', TypeDetailView.as_view(), name='type_detail'),
    path('type/modify/', TypeModifyView.as_view(), name='type_modify')
]
