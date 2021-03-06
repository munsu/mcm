import csv
import json
import logging
import traceback
import twilio.twiml

from datetime import timedelta

from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import Count, DateField
from django.db.models.functions import Cast
from django.http import HttpResponseRedirect, HttpResponse
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import ugettext as _
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import ListView, DetailView, TemplateView
from django.views.generic.edit import FormView, UpdateView, DeleteView

from braces.views import JSONResponseMixin
from crispy_forms.helper import FormHelper
# from extra_views import FormSetView
from extra_views import CreateWithInlinesView, UpdateWithInlinesView, InlineFormSet
from rest_framework import exceptions as drf_exceptions
from rest_framework import mixins, permissions, status, views, viewsets
from rest_framework.authentication import BasicAuthentication
from rest_framework.decorators import list_route
from rest_framework.response import Response
from rest_framework.settings import api_settings

from .forms import AppointmentsUploadForm, MessageTemplateForm, ProtocolForm, UpdateMessageTemplateForm
from .models import Appointment, Protocol, Message, MessageAction, Constraint, MessageTemplate
from .serializers import AppointmentSerializer, ProtocolSerializer, DayAfterAppointmentSerializer
from .tasks import send_sms
from .utils import language

logger = logging.getLogger(__name__)


def send_sms_view(request):
    if request.method == "POST":
        body = request.POST.get('body')
        to = request.POST.get('phone')
        print "MSG REQ", body, to
        print send_sms(body, to)
    return HttpResponseRedirect(reverse('home'))


class IndexView(LoginRequiredMixin, ListView):
    template_name = 'index.html'
    model = Appointment


class UnconfirmedView(LoginRequiredMixin, ListView):
    template_name = 'unconfirmed.html'
    model = Appointment


class CanceledView(LoginRequiredMixin, ListView):
    template_name = 'canceled.html'
    model = Appointment

class ReportsView(LoginRequiredMixin, ListView):
    template_name = 'reports.html'
    model = Appointment


class AppointmentsView(views.APIView):
    permission_classes = (permissions.IsAuthenticated, )

    def get(self, request, *args, **kwargs):
        num_days = int(request.GET.get('days', 10))
        offset = int(request.GET.get('offset', 0))
        show_only = []
        for status in ['confirmed', 'unconfirmed', 'cancelled']:
            if int(request.GET.get(status, 1)):
                show_only.append(status)
        now = timezone.now() + timedelta(days=offset*num_days)
        dates = [now.date() + timedelta(days=n) for n in range(num_days)]
        appointments = (Appointment.objects
            .annotate(date=Cast('appointment_date', DateField()))
            .filter(date__range=(dates[0], dates[-1]),
                    appointment_confirm_status__in=show_only)
            .order_by('date')
        )
        return Response({
            'appointments': [a.as_row() for a in appointments],
            'range_str': "{} - {}".format(dates[0].strftime('%B %d'), dates[-1].strftime('%B %d, %Y')),
        })


class AppointmentDetailView(LoginRequiredMixin, DetailView):
    model = Appointment


class AppointmentUpdateStatusView(LoginRequiredMixin, UpdateView):
    model = Appointment
    fields = ['appointment_confirm_status', 'notes']
    template_name_suffix = "_update_status_form"

    def get_success_url(self):
        return reverse('appointments:detail', args=[self.object.id])

    def get_context_data(self, **kwargs):
        context = super(AppointmentUpdateStatusView, self).get_context_data(**kwargs)
        context['queued_messages'] = self.object.messages.filter(
            twilio_status=Message.TWILIO_STATUS.queued)
        return context

    def form_valid(self, form):
        # TODO get only updated fields
        message = "\n".join(["{}: {}".format(field, form.data[field]) for field in self.fields])
        self.object.messages_log.create(
            sender='system',
            body='Appointment updated by {}:\n{}'.format(
                self.request.user, message))
        return super(AppointmentUpdateStatusView, self).form_valid(form)


class ConfirmReportView(views.APIView):
    permission_classes = (permissions.IsAuthenticated, )

    def get(self, request, *args, **kwargs):
        num_days = int(request.GET.get('days', 10))
        offset = int(request.GET.get('offset', 0))
        now = timezone.now() + timedelta(days=offset*num_days)
        dates = [now.date() + timedelta(days=n) for n in range(num_days)]
        datasets = {
            status[0]: [0] * num_days
            for status in Appointment.APPOINTMENT_CONFIRM
        }
        totals = [0] * num_days
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
            totals[dates.index(c['date'])] += c['count']
        return Response({
            'labels': [date.strftime('%b %d') for date in dates],
            'datasets': datasets,
            'totals': totals,
            'range_str': "{} - {}".format(dates[0].strftime('%B %d'), dates[-1].strftime('%B %d, %Y')),
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
        return super(AppointmentViewSet, self).dispatch(request, *args, **kwargs)

    def perform_create(self, serializer):
        serializer.save(client=self.request.user.profile.client)

    @list_route(methods=['POST'])
    def batch_file(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, many=True)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class AppointmentsUploadFormView(SuccessMessageMixin, FormView):
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

    def get_success_message(self, cleaned_data):
        file = cleaned_data.get('file')
        appointments_data = []
        reader = csv.DictReader(file)
        for line in reader:
            line = {k.lower(): v for k, v in line.iteritems() if v}
            appointments_data.append(line)
        return "Updated {} appointments.".format(len(appointments_data))


class DayAfterAppointmentsUploadFormView(SuccessMessageMixin, FormView):
    template_name = 'appointments/upload.html'
    form_class = AppointmentsUploadForm

    def form_valid(self, form):
        file = form.cleaned_data.get('file')
        day_after_appointments_data = []
        reader = csv.DictReader(file)
        for line in reader:
            line = {k.lower(): v for k, v in line.iteritems() if v}
            day_after_appointments_data.append(line)
            print json.dumps(line)
        serializer = DayAfterAppointmentSerializer(data=day_after_appointments_data, many=True, context={'request': self.request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        # serializer = AppointmentSerializer(data=appointments_data, many=True)
        # serializer.is_valid(raise_exception=True)
        # serializer.save(client=self.request.user.profile.client)
        # print serializer.data

        # TODO return number of created appointments.
        return super(DayAfterAppointmentsUploadFormView, self).form_valid(form)

    def get_success_url(self):
        return reverse('home')

    def get_success_message(self, cleaned_data):
        file = cleaned_data.get('file')
        day_after_appointments_data = []
        reader = csv.DictReader(file)
        for line in reader:
            line = {k.lower(): v for k, v in line.iteritems() if v}
            day_after_appointments_data.append(line)
        return "Updated {} appointments.".format(len(day_after_appointments_data))


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
        print request.data
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def perform_create(self, serializer):
        instance = serializer.save()
        self.request.user.profile.clients.add(instance)

    def get_success_headers(self, data):
        try:
            return {'Location': data[api_settings.URL_FIELD_NAME]}
        except (TypeError, KeyError):
            return {}


class ProtocolsListView(ListView):
    template_name = 'appointments/protocols-list.html'
    model = Protocol

    def get_queryset(self):
        return self.model.objects.filter(clients=self.request.user.profile.client)


class ConstraintsInline(InlineFormSet):
    model = Constraint
    fields = '__all__'
    extra = 1


class MessageActionInline(InlineFormSet):
    model = MessageAction
    fields = '__all__'
    extra = 1


class ProtocolsDetailView(UpdateWithInlinesView):
    template_name = 'appointments/protocols-detail.html'
    model = Protocol
    fields = ('name', 'priority', 'constraint_relationship',)
    inlines = [ConstraintsInline]

    def get_context_data(self, **kwargs):
        context = super(ProtocolsDetailView, self).get_context_data(**kwargs)
        context['message_templates'] = self.get_object().templates.all()
        return context


class MessageTemplatesListView(ListView):
    template_name = 'appointments/templates-list.html'
    model = MessageTemplate

    def get_queryset(self):
        return self.model.objects.filter(protocol__clients=self.request.user.profile.client)


class MessageTemplatesCreateView(CreateWithInlinesView):
    template_name = 'appointments/templates-create.html'
    model = MessageTemplate
    # fields = '__all__'
    # exclude = ('content', 'content_tail')
    form_class = MessageTemplateForm
    inlines = [MessageActionInline]

    def get_context_data(self, **kwargs):
        context = super(MessageTemplatesCreateView, self).get_context_data(**kwargs)
        context['protocol'] = Protocol.objects.get(id=context['protocol_pk'])
        return context

    def get_initial(self):
        return {'protocol': self.kwargs.get('protocol_pk')}


class MessageTemplatesDetailView(UpdateWithInlinesView):
    template_name = 'appointments/templates-detail.html'
    model = MessageTemplate
    # fields = '__all__'
    # exclude = ('content', 'content_tail')
    form_class = UpdateMessageTemplateForm
    inlines = [MessageActionInline]

    def post(self, request, *args, **kwargs):
        if self.request.POST.get('delete'):
            self.object = self.get_object()
            self.object.delete()
            return HttpResponseRedirect(reverse('protocols:detail', args=[self.kwargs['protocol_pk']]))
        return super(MessageTemplatesDetailView, self).post(request, *args, **kwargs)


class ManageProtocolsView(UpdateWithInlinesView):
    template_name = 'appointments/protocols-list.html'
    model = Protocol

    # def get_queryset(self):
    #     return self.model.objects.filter(clients=self.request.user.profile.client)


def twilio_reply(request):
    """TODO specific to client twilio number"""
    sender = settings.TWILIO_NUMBER
    ack_msg = "OK"  # TODO direct to doctor's office
    try:
        logger.info("<twilio_reply>:{}".format(request.GET))
        from_number = request.GET.get('From', None)
        body = request.GET.get('Body', None)
        to = request.GET.get('To', None)  # TODO integrate this
        m = Message.objects.filter(
            appointment__patient__patient_mobile_phone=from_number,
            twilio_status=Message.TWILIO_STATUS.delivered,
            ).last()
        c = m.appointment.client
        r = m.reply_set.create(content=body)

        # TODO place this somewhere else.
        m.appointment.messages_log.create(
            sender='patient',
            body=body)

        # TODO check if there is no messageaction
        if r.message_action is None:
            # not valid
            logger.info(u"resending tail:{}".format(m.tail))
            ack_msg = m.tail
        elif r.message_action.action == MessageAction.ACTION.confirm:
            with language(m.appointment.patient.lang):
                ack_msg = _("Thank you for confirming the appointment.")
        elif r.message_action.action == MessageAction.ACTION.reschedule:
            with language(m.appointment.patient.lang):
                ack_msg = _("Doctor's Office\n{}\n{}")
                ack_msg = ack_msg.format(
                    m.appointment.appointment_provider.get_contact_details,
                    m.appointment.appointment_provider.get_office_hours)
        elif r.message_action.action == MessageAction.ACTION.cancel:
            """
            provider
            phone numbers
            hours
            """
            with language(m.appointment.patient.lang):
                ack_msg = _("We're sorry to hear that - We can connect you to "
                            "our office and reschedule your appointment at\n{}\n{}")
                ack_msg = ack_msg.format(
                    m.appointment.appointment_provider.get_contact_details,
                    m.appointment.appointment_provider.get_office_hours)
        elif r.message_action.action == MessageAction.ACTION.lang:
            ack_msg = m.body
        m.appointment.messages_log.create(
            sender='client',
            body=ack_msg)
    except Exception as e:
        logger.info(e)
        logger.error(traceback.format_exc())
    resp = twilio.twiml.Response()
    resp.message(msg=ack_msg, sender=settings.TWILIO_NUMBER)
    return HttpResponse(resp)


def twilio_voice(request, appointment_message_id=None):
    try:
        message = Message.objects.get(id=appointment_message_id)
        text = message.body
    except Message.DoesNotExist:
        text = "Hello"

    resp = twilio.twiml.Response()
    resp.say(text=text)
    return HttpResponse(resp)
