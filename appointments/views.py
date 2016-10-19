from datetime import timedelta

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, DateField
from django.db.models.functions import Cast
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils import timezone
from django.views.generic import TemplateView

from braces.views import JSONResponseMixin
from rest_framework import views, viewsets, status, permissions
from rest_framework.response import Response
from rest_framework.settings import api_settings

from .tasks import send_sms
from .models import Appointment
from .serializers import AppointmentSerializer


def send_sms_view(request):
    if request.method == "POST":
        body = request.POST.get('body')
        to = request.POST.get('phone')
        print "MSG REQ", body, to
        print send_sms(body, to)
    return HttpResponseRedirect(reverse('home'))


class IndexView(LoginRequiredMixin, TemplateView):
    template_name = 'index.html'


class ConfirmReportView(views.APIView):
    permission_classes = (permissions.IsAuthenticated, )

    def get(self, request, *args, **kwargs):
        num_days = 7
        now = timezone.now()
        dates = [
            date for date in
            [now.date() + timedelta(days=n) for n in range(num_days)]
        ]
        datasets = {
            status[0]: [0] * num_days
            for status in Appointment.APPOINTMENT_CONFIRM_CHOICES
        }
        confirmations = (
            Appointment.objects
            .annotate(date=Cast('appointment_date', DateField()))
            .filter(date__range=(dates[0], dates[-1]))
            .order_by('date', 'appointment_confirm_status')
            .values('appointment_confirm_status', 'date')
            .annotate(count=Count('id'))
        )
        for c in confirmations:
            datasets[c['appointment_confirm_status']][dates.index(c['date'])] = c['count']
        return Response({
            'labels': [date.strftime('%b %d') for date in dates],
            'datasets': datasets,
        })


class AppointmentViewSet(viewsets.GenericViewSet):
    serializer_class = AppointmentSerializer
    queryset = Appointment.objects.all()
    permission_classes = (permissions.IsAuthenticated, )

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
