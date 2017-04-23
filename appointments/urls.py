"""mcm URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.10/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url, include
from django.contrib import admin
from . import views

from rest_framework.routers import DefaultRouter
from rest_framework.schemas import get_schema_view


router = DefaultRouter()
router.register(r'ppointments', views.AppointmentViewSet)

protocol_router = DefaultRouter()
protocol_router.register(r'otocols', views.ProtocolsViewSet, base_name='protocols')

appointments = [
    url(r'^(?P<pk>\d+)/$', views.AppointmentUpdateStatusView.as_view(), name='detail'),
    url(r'^ctionables/$', views.AppointmentsView.as_view(), name='actionables'),
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    url(r'^send_sms/$', views.send_sms_view, name='send_sms'),
    url(r'^reports/', include([
        url(r'^confirm/$', views.ConfirmReportView.as_view(), name='confirm')
    ], namespace='reports')),
    url(r'^upload/', include([
        url(r'^csv/$', views.AppointmentsUploadFormView.as_view(), name='csv'),
        url(r'^csv/day_after/$', views.DayAfterAppointmentsUploadFormView.as_view(), name='day-after-csv')
    ], namespace='upload')),
    url(r'^', include(router.urls)),
]

protocols = [
    url(r'^r/', include(protocol_router.urls)),
    url(r'^$', views.ProtocolsListView.as_view(), name='list'),
    url(r'^(?P<pk>\d+)/$', views.ProtocolsDetailView.as_view(), name='detail'),
    url(r'^t/$', views.MessageTemplatesListView.as_view(), name='templates-list'),
    url(r'^(?P<protocol_pk>\d+)/t/new/$', views.MessageTemplatesCreateView.as_view(), name='templates-create'),
    url(r'^(?P<protocol_pk>\d+)/t/(?P<pk>\d+)/$', views.MessageTemplatesDetailView.as_view(), name='templates-detail'),
    url(r'^rotocols/$', views.ManageProtocolsView.as_view(), name='manage'),
]

# schema_view = get_schema_view(title="Server Monitoring API")

urlpatterns = [
    url(r'^$', views.IndexView.as_view(), name='home'),
    url(r'^unconfirmed/$', views.UnconfirmedView.as_view(), name='unconfirmed'),
    url(r'^canceled/$', views.CanceledView.as_view(), name='canceled'),
    url(r'^reports/$', views.ReportsView.as_view(), name='reports-tab'),
    url(r'^t/$', views.twilio_reply, name='twilio'),
    url(r'^v/$', views.twilio_voice, name='twilio-voice'),
    url(r'^v/(?P<appointment_message_id>\d+)/$', views.twilio_voice, name='twilio-voice-detail'),
    url(r'^a/', include(appointments, namespace='appointments')),
    url(r'^p/', include(protocols, namespace='protocols')),
    # url(r'^i/$', schema_view),
]
