# created by Chirath R, chirath.02@gmail.com
# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import datetime
from smtplib import SMTPException

from django.contrib.auth.models import User
from django import forms
from django.contrib.sites.shortcuts import get_current_site
from django.forms.utils import ErrorList
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse, reverse_lazy
from django.views import View
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.core.mail import send_mail
from django.core.mail import EmailMessage

from promotion.forms import JoinApplicationForm
from promotion.models import JoinApplication
from fosswebsite.settings import join_application_mail_list, join_application_reply_to

approve_mail_content = ',\\n\\nWe are excited to inform that you are selected for the interview. Be there at ' + \
                        'ground floor computer lab by 5PM. \\n\\nIf you have any queries contact : Chirath,'+ \
                        ' 8547801861 \\n\\nThank you, \\n\\nFOSS@Amrita'

reject_mail_content = ',\\n\\nWe are sorry to inform that you are not selected for the interview. Please try again ' \
                      'next time.'


class JoinApplicationListView(ListView):
    model = JoinApplication
    queryset = JoinApplication.objects.filter(is_approved=False, is_rejected=False).order_by('-date')

    def get_context_data(self, **kwargs):
        context = super(JoinApplicationListView, self).get_context_data(**kwargs)
        context['count'] = len(context['object_list'])
        status = self.request.GET.get('list', None)
        year = self.request.GET.get('year', None)
        if year == '1':
            context['object_list'] = JoinApplication.objects.filter(batch="1st year").order_by('-date')
            context['count'] = len(context['object_list'])

        if year == '2':
            context['object_list'] = JoinApplication.objects.filter(batch="2nd year").order_by('-date')
            context['count'] = len(context['object_list'])

        if status == "approved":
            context['object_list'] = JoinApplication.objects.filter(is_approved=True).order_by('-date')
            context['count'] = len(context['object_list'])

        if status == "rejected":
            context['object_list'] = JoinApplication.objects.filter(is_rejected=True).order_by('-date')
            context['count'] = len(context['object_list'])
        return context


class JoinApplicationDetailView(DetailView):
    errors = None
    model = JoinApplication

    def get_context_data(self, **kwargs):
        context = super(JoinApplicationDetailView, self).get_context_data(**kwargs)
        context['approve_mail_subject'] = 'Congrats! FOSS@Amrita membership application'
        context['approve_mail_content'] = 'Hi ' + self.get_object().name + approve_mail_content
        context['reject_mail_subject'] = 'FOSS@Amrita membership application'
        context['reject_mail_content'] = 'Hi ' + self.get_object().name + reject_mail_content
        context['mail_error'] = self.request.GET.get('errors', None)
        return context


class JoinApplicationCreateView(CreateView):
    form_class = JoinApplicationForm
    template_name = 'base/form.html'
    success_url = reverse_lazy('join_success')

    def get_context_data(self, **kwargs):
        context = super(JoinApplicationCreateView, self).get_context_data(**kwargs)
        context['title'] = 'Applications'
        context['heading'] = 'Membership Application'
        return context

    def form_valid(self, form):

        try:
            application = JoinApplication.objects.filter(email=form.cleaned_data.get('email'))
        except JoinApplication.DoesNotExist:
            application = None

        if application.exists():
            form._errors[forms.forms.NON_FIELD_ERRORS] = ErrorList([
                u'Your application is already submitted'
            ])
            return self.form_invalid(form)

        valid_form = super(JoinApplicationCreateView, self).form_valid(form)

        # generate urls
        # list_url = ''.join(['http://', get_current_site(self.request).domain, reverse('join_list')])
        #
        # # mail data
        # subject = 'Application from ' + form.cleaned_data.get('name')
        # content = 'A new application was submitted by ' + form.cleaned_data.get('name') + ' at ' + \
        #           str(datetime.datetime.now()) + '. \n\nPlease visit ' + list_url + ' for more details.'
        #
        # to_address_list = list(User.objects.filter(is_superuser=True).values_list('email', flat=True))
        #
        # # sent mail when application is submitted
        # send_mail(subject, content, 'amritapurifoss@gmail.com', to_address_list, fail_silently=False)

        mail_content = "Hi " + form.cleaned_data.get('name') + ", \n\n" + \
                       "Great to know that you are interested in being a part of the FOSS club at Amritapuri. " + \
                       "We got your application, please complete the " + \
                       "tasks at [1] and complete at least 25 Hackerrank[2] problems or " + \
                       "if you are not familiar with programming complete cs50.tv[3] till week 3 " + \
                       "before " + str(datetime.date.today() + datetime.timedelta(days=20)) + ".\n\n" + \
                       "Let us know when you are done with the Hackerrank problems, so that we can have a one on " + \
                       "one interview. We won't be testing your skills but would ask about the problems you have " + \
                       "solved. This is to test if you are really interested and we expect you to be honest. " + \
                       "If you have any queries feel free to reply to this mail." + \
                       "\n\n[1] http://foss.amrita.ac.in/foss/#sixth\n[2] https://www.hackerrank.com/" + \
                       "\n[3] http://cs50.tv/2016/fall/\n\nWith regards, \n\nFOSS@Amrita"
        to_address_list = ['chirath.02@gmail.com', form.cleaned_data.get('email')]
        email = EmailMessage(
            'Tasks to complete, FOSS@Amrita',
            mail_content,
            'amritapurifoss@gmail.com',
            to_address_list,
            join_application_mail_list,
            reply_to=join_application_reply_to,
            headers={'Message-ID': 'foss@amrita'},
        )
        email.send(fail_silently=False)
        to_address_list.remove(form.cleaned_data.get('email'))
        return valid_form


class EmailForm(forms.Form):
    mail_id = forms.EmailField()
    mail_subject = forms.CharField()
    mail_content = forms.CharField()


class JoinApplicationUpdateView(UpdateView):
    """
    Approve or reject application, sends mail to the applicant and all admin users.
    """
    model = JoinApplication
    fields = ['is_approved']

    def get(self, **kwargs):
        return HttpResponse('This view accepts only post requests')

    def post(self, request, *args, **kwargs):
        if not (request.user.is_superuser or request.user == self.get_object().created_by):
            return redirect('permission_denied')
        errors = None
        form = EmailForm(request.POST)
        if form.is_valid():
            # mail id of all the admins and the mail id from the form
            to_address_list = list(User.objects.filter(is_superuser=True).values_list('email', flat=True))
            to_address_list.append(form.cleaned_data['mail_id'])

            # sent mail, if there are errors in mail, check that too
            try:
                send_mail(form.cleaned_data['mail_subject'], form.cleaned_data['mail_content'],
                          'amritapurifoss@gmail.com', to_address_list, fail_silently=False)
                join_application = self.get_object()

                # approve
                if request.POST.get('is_approved', None):
                    join_application.is_approved = True

                # reject
                if request.POST.get('is_rejected', None):
                    join_application.is_rejected = True

                # save
                join_application.save()
            except SMTPException:
                errors = 'Mail not sent, mail id might be wrong'

            # render the detail page
            if not errors:
                return redirect(reverse('join_detail', kwargs={'pk': self.get_object().id}))
        else:
            errors = "The given mail is invalid, try again"
        # error in form
        return redirect(reverse('join_detail', kwargs={'pk': self.get_object().id}) + '?errors=' + errors)


class ContactView(View):
    def get(self, request):
        template_name = 'promotion/index.html'
        return render(request, template_name)

    def post(self, request):
        subject = 'Message from ' + request.POST.get('name')
        content = "Message from : " + request.POST.get('name') + " <" + request.POST.get('email') + ">\n\n" +\
                  request.POST.get('message')
        to_address_list = list(User.objects.filter(is_superuser=True).values_list('email', flat=True))
        send_mail(subject, content, 'amritapurifoss@gmail.com', to_address_list, fail_silently=True)
        return render(request, template_name='promotion/index.html', context={"is_success": True})


def validate_mail(email):
    from django.core.validators import validate_email
    from django.core.exceptions import ValidationError
    try:
        validate_email(email)
        return True
    except ValidationError:
        return False


class EmailAllApplicantsView(View):
    def get(self, request):
        template_name = 'promotion/mail_to_all.html'
        to_list = ""
        bcc_list = "vipin.p@gmail.com, "
        cc_list = ""

        for application in JoinApplication.objects.filter(is_approved=False, is_rejected=False):
            to_list += application.email + ", "

        for user in User.objects.filter(is_superuser=True):
            cc_list += user.email + ", "

        reply_to = join_application_reply_to[0]
        mail_subject = "FOSS@Amrita"
        mail_content = "Namah Shivaya, \n\n"

        context = {'to_list': to_list, 'bcc_list': bcc_list, 'cc_list': cc_list,
                   'reply_to': reply_to, 'mail_subject': mail_subject, 'mail_content': mail_content}
        return render(request, template_name, context)

    def post(self, request):
        template_name = 'promotion/mail_sent.html'

        to_list = request.POST['to_list'].strip()
        bcc_list = request.POST['bcc_list'].strip()
        cc_list = request.POST['cc_list'].strip()

        to_list = to_list.strip(",")
        bcc_list = bcc_list.strip(",")
        cc_list = cc_list.strip(",")

        mail_subject = request.POST['mail_subject'].strip()
        mail_content = request.POST['mail_content'].strip()

        error = ""
        # validation of all mail id

        to = to_list.split(",")
        for i in range(len(to)):
            to[i] = to[i].strip()
            if not validate_mail(to[i]):
                print(to)
                error += "to list: mail id not valid - " + to[i]

        bcc = bcc_list.split(",")
        for i in range(len(bcc)):
            bcc[i] = bcc[i].strip()
            if not validate_mail(bcc[i]):
                print(bcc)
                error += "bcc list: mail id not valid - " + bcc[i]

        cc = cc_list.split(",")
        for i in range(len(cc)):
            cc[i] = cc[i].strip()
            if not validate_mail(cc[i]):
                error += "cc list: mail id not valid - " + cc[i]

        context = {'to_list': to_list, 'bcc_list': bcc_list, 'cc_list': cc_list,
                   'mail_subject': mail_subject, 'mail_content': mail_content}

        if error != "":
            context["error"] = error
            template_name = 'promotion/mail_to_all.html'
            return render(request, template_name, context)

        email = EmailMessage(
            mail_subject,
            mail_content,
            'amritapurifoss@gmail.com',
            to + cc,
            bcc,
            headers={'Message-ID': 'foss@amrita'},
        )
        email.send(fail_silently=True)
        return render(request, template_name, context)
