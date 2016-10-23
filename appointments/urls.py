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

router = DefaultRouter()
router.register(r'ppointments', views.AppointmentViewSet)

protocol_router = DefaultRouter()
protocol_router.register(r'rotocols', views.ProtocolsViewSet, base_name='protocols')

appointments = [
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    url(r'^send_sms/$', views.send_sms_view, name='send_sms'),
    url(r'^reports/', include([
        url(r'^confirm/$', views.ConfirmReportView.as_view(), name='confirm')
    ], namespace='reports')),
    url(r'^upload/', include([
        url(r'^csv/$', views.AppointmentsUploadFormView.as_view(), name='csv')
    ], namespace='upload')),
    url(r'^', include(router.urls)),
]

protocols = [
    url(r'^', include(protocol_router.urls)),
]

urlpatterns = [
    url(r'^$', views.IndexView.as_view(), name='home'),
    url(r'^a/', include(appointments, namespace='appointments')),
    url(r'^p/', include(protocols, namespace='protocols')),
]
