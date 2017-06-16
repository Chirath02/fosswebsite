# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from datetime import date, datetime

from django.contrib.auth.models import User
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views.generic import View, CreateView, UpdateView, DeleteView, ListView, DetailView
from clubManagement.models import Attendance, Responsibility
from registration.models import UserInfo

month = ["January", "February", "March", "April", "May", "June", "July", "August", "September",
         "October", "November", "December"]

month_num = range(12)


def calculate_year(year):
    year = datetime.now().year - year
    if datetime.now().month > 5:
        year += 1
    print(year)
    if year == 1:
        return '1st year'
    elif year == 2:
        return '2nd year'
    elif year == 3:
        return '3rd year'
    elif year == 4:
        return '4th year'
    else:
        return 'Alumni - ' + str(year + datetime.now().year) + ' batch'


def get_batch_list(kwargs):
    batches = []
    if 'batch' in kwargs:
        batches += [int(kwargs.get('batch'))]
    else:
        year = datetime.now().year
        if datetime.now().month < 5:
            year -= 1
        for i in range(4):
            batches += [year - i]
    print(batches)
    return batches


class AttendanceAddView(View):
    template_name = 'clubManagement/attendance_add.html'

    def get(self, request, **kwargs):
        """
        A view for an admin to add attendance for a particular date.
        url = /batch/year/month/day/
        or
        url = /year/month/day (display 1st - 4th year)
        date is calculated from (year, month, day)
        and students is selected according to batch

        attendance_list = [ [ '1st_year', list_of_1st_years ], ..... ]
        """
        if not request.user.is_authenticated:
            return redirect('permission_denied')

        d = date(int(kwargs.get('year')), int(kwargs.get('month')), int(kwargs.get('day')))
        context = {}
        batch_list = get_batch_list(kwargs)

        attendance_list = []

        for batch in batch_list:
            user_info_list = UserInfo.objects.filter(year=batch)
            # display the current attendance for this date and batch
            attendance_list_batch = []
            for user_info in user_info_list:
                try:
                    attendance = Attendance.objects.get(user=user_info.user, date=d)
                except Attendance.DoesNotExist:
                    attendance = Attendance(user=user_info.user,
                                            added_by=User.objects.get(username=self.request.user.username), date=d)
                    attendance.save()
                attendance_list_batch.append(attendance)

            # attendance list contains all the Attendance objects of the batch with date = d
            year = calculate_year(batch)
            attendance_list += [[attendance_list_batch, year], ]

        context = {'attendance_list': attendance_list}
        print(context)
        return render(request, self.template_name, context)

    def post(self, request, **kwargs):
        if not request.user.is_superuser:
            return redirect('permission_denied')

        d = date(int(kwargs.get('year')), int(kwargs.get('month')), int(kwargs.get('day')))

        if 'batch' in kwargs:
            user_info_list = UserInfo.objects.filter(year=int(kwargs.get('batch')))
            for user_info in user_info_list:
                attendance_list = user_info.user.attendance_set.filter(date=d)
                for i in attendance_list:
                    i.attendance = False
                    i.save()
        else:
            # make all attendance false and make attendance = true for users in request.POST.
            attendance_list = Attendance.objects.filter(date=d)
            for i in attendance_list:
                i.attendance = False
                i.save()

        for key in request.POST:
            try:
                user = User.objects.get(username=key)
            except User.DoesNotExist:
                user = None
            if user:
                att = Attendance.objects.get(user=user, date=d)
                att.attendance = True
                att.save()
        if 'batch' in kwargs:
            return redirect('add_attendance_batch', **kwargs)
        else:
            return redirect('add_attendance_all', **kwargs)


class YearStudentAttendanceReportView(View):
    template_name = 'clubManagement/attendance_yearly.html'

    def get(self, request, **kwargs):
        user = User.objects.get(id=int(kwargs.get('user_id')))
        att = user.attendance_set.filter(date__year=int(kwargs.get('year')))
        if len(att) > 0:
            month_att = []
            for i in month_num:
                month_att.append(len(att.filter(date__month=(i + 1))))
            context = {'user': user, 'month_att': month_att, 'month': month, 'month_num': month_num,
                       'year': kwargs.get('year')}
        else:
            context = {'errors', 'No records found'}
        return render(request, self.template_name, context)


class YearAttendanceReportView(View):
    """
    context = {'data_list': data_list}
    where:
        data_list = [ [user_data, year, error], ....]
        user_data = [[user, month_att, total_att], ......]
        month_att = list of attendance for 12 months
    """
    template_name = 'clubManagement/attendance_batch_yearly.html'

    def get(self, request, **kwargs):
        batch_list = get_batch_list(kwargs)
        data_list = []
        for batch in batch_list:
            user_info_list = UserInfo.objects.filter(year=batch)
            user_data = []
            for user_info in user_info_list:
                month_att = []
                total_att = 0
                for i in month_num:
                    att_month = len(
                        user_info.user.attendance_set.filter(
                            date__year=int(kwargs.get('year')),
                            date__month=(i + 1),
                            attendance=True
                        )
                    )
                    total_att += att_month
                    month_att.append(att_month)
                user_data.append([user_info.user, month_att, total_att])
            year = calculate_year(batch)
            if len(user_data) > 0:
                data_list.append([user_data, year, ''])
            else:
                data_list.append([user_data, year, 'No record found'])
        context = {'data_list': data_list}
        return render(request, self.template_name, context)


# Responsibilities
# CreateView and UpdateView calls get_absolute_url() on the model to get the success_url
class ResponsibilityListView(ListView):
    model = Responsibility


class ResponsibilityDetailView(DetailView):
    model = Responsibility


class ResponsibilityCreateView(CreateView):
    model = Responsibility
    fields = ['created_by', 'name', 'description']

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        return super(ResponsibilityCreateView, self).form_valid(form)


class ResponsibilityUpdateView(UpdateView):
    model = Responsibility
    fields = ['name', 'description']


class ResponsibilityDeleteView(DeleteView):
    model = Responsibility
    success_url = reverse_lazy('responsibility')
