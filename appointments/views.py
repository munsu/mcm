import csv
import json

from datetime import timedelta

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, DateField
from django.db.models.functions import Cast
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils import timezone
from django.views.generic import TemplateView, DetailView
from django.views.generic.edit import FormView
from django.views.generic.list import ListView

from braces.views import JSONResponseMixin
from rest_framework import exceptions as drf_exceptions
from rest_framework import mixins, permissions, status, views, viewsets
from rest_framework.decorators import list_route
from rest_framework.response import Response
from rest_framework.settings import api_settings

from .forms import AppointmentsUploadForm
from .models import Appointment, Protocol
from .serializers import AppointmentSerializer, ProtocolSerializer
from .tasks import send_sms


def send_sms_view(request):
    if request.method == "POST":
        body = request.POST.get('body')
        to = request.POST.get('phone')
        print "MSG REQ", body, to
        print send_sms(body, to)
    return HttpResponseRedirect(reverse('home'))


class IndexView(LoginRequiredMixin, TemplateView):
    template_name = 'index.html'


class AppointmentDetailView(LoginRequiredMixin, DetailView):
    model = Appointment


class ConfirmReportView(views.APIView):
    permission_classes = (permissions.IsAuthenticated, )

    def get(self, request, *args, **kwargs):
        num_days = int(request.GET.get('days', 7))
        now = timezone.now()
        dates = [now.date() + timedelta(days=n) for n in range(num_days)]
        datasets = {
            status[0]: [0] * num_days
            for status in Appointment.APPOINTMENT_CONFIRM_CHOICES
        }
        confirmations = (
            Appointment.objects
            .annotate(date=Cast('appointment_date', DateField()))
            .filter(date__range=(dates[0], dates[-1]))
            .order_by('date', 'appointment_confirm_status')
            .values('date', 'appointment_confirm_status')
            .annotate(count=Count('id'))
        )
        for c in confirmations:
            datasets[c['appointment_confirm_status']][dates.index(c['date'])] = c['count']
        return Response({
            'labels': [date.strftime('%b %d') for date in dates],
            'datasets': datasets,
        })


class AppointmentViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    serializer_class = AppointmentSerializer
    queryset = Appointment.objects.all()
    permission_classes = (permissions.IsAuthenticated, )

    def dispatch(self, request, *args, **kwargs):
        try:
            if request.user.profile.client is None:
                raise drf_exceptions.PermissionDenied()
        except Exception:
            print "TODO this exception"
        return super(ProtocolsViewSet, self).dispatch(request, *args, **kwargs)

    def perform_create(self, serializer):
        serializer.save(client=self.request.user.profile.client)

    @list_route(methods=['POST'])
    def batch_file(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, many=True)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class AppointmentsUploadFormView(FormView):
    template_name = 'appointments/upload.html'
    form_class = AppointmentsUploadForm

    def form_valid(self, form):
        file = form.cleaned_data.get('file')
        appointments_data = []
        reader = csv.DictReader(file)
        for line in reader:
            line = {k.lower(): v for k, v in line.iteritems()}
            appointments_data.append(line)
            # print json.dumps(line)
        serializer = AppointmentSerializer(data=appointments_data, many=True)
        serializer.is_valid(raise_exception=True)
        serializer.save(client=self.request.user.profile.client)
        print serializer.data

        # TODO return number of created appointments.
        return super(AppointmentsUploadFormView, self).form_valid(form)

    def get_success_url(self):
        return reverse('home')


class ProtocolsViewSet(viewsets.GenericViewSet):
    serializer_class = ProtocolSerializer
    # queryset = Protocol.objects.all()
    permission_classes = (permissions.IsAuthenticated, )

    def dispatch(self, request, *args, **kwargs):
        try:
            if request.user.profile.client is None:
                raise drf_exceptions.PermissionDenied()
        except Exception:
            print "TODO this exception"
        return super(ProtocolsViewSet, self).dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return Protocol.objects.filter(clients=self.request.user.profile.client)

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    # def get_queryset(self):
    #     # return protocol -> messagetemplate -> messageaction
    #     return requ

    def create(self, request, *args, **kwargs):
        if request.user.profile.client is None:
            return Response('User has no client', status=status.HTTP_401_UNAUTHORIZED)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def perform_create(self, serializer):
        serializer.save(client=self.request.user.profile.client)

    def get_success_headers(self, data):
        try:
            return {'Location': data[api_settings.URL_FIELD_NAME]}
        except (TypeError, KeyError):
            return {}



