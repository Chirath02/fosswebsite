from django.conf.urls import url
from django.views.generic import TemplateView
from registration.views import UserSignUpView, login, ProfileView

urlpatterns = [
    url(r'^login/$', login, name="login"),
    url(r'^(?P<pk>\d+)$', ProfileView.as_view(template_name = 'profile/profile.html'), name="profile"),
    url(r'^signup/$', UserSignUpView.as_view(), name="signup"),
    url(
        r'^signup/success$',
        TemplateView.as_view(template_name='registration/signup_success.html'),
        name="signup_success"
    ),
    url(
        r'^signup/already-logged-in',
        TemplateView.as_view(template_name='registration/already_logged_in.html'),
        name="already_logged_in"
    ),
    url(
        r'^signup/permission-denied',
        TemplateView.as_view(template_name='registration/permission_denied.html'),
        name="permission_denied"
    ),
]
