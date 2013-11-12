# Django
from django.contrib.auth import authenticate, login, logout
from django.views.generic.edit import FormView
from django.shortcuts import redirect, render
from django.core.urlresolvers import reverse, reverse_lazy
from django.contrib import messages

# Project App
from frontend.forms import LoginForm

def frontend_home(request):
    return render(request,
                  "frontend/home.html")


def logout_user(request):
    logout(request)
    messages.success(request, "You have been successfully logged out")
    return redirect(reverse("frontend_home"))


class LoginUserView(FormView):
    template_name = 'frontend/login.html'
    form_class = LoginForm
    success_url = reverse_lazy("frontend_home")

    def dispatch(self, request, *args, **kwargs):
        return super(LoginUserView, self).dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        # Pass request to get_form_class and get_form for per-request
        # form control.
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        return self.render_to_response(self.get_context_data(form=form))

    def post(self, request, *args, **kwargs):
        # Pass request to get_form_class and get_form for per-request
        # form control.
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        if form.is_valid():
            # Pass request to form_valid.
            user = authenticate(username=form.cleaned_data['email'],
                                password=form.cleaned_data['password'])
            if user:
                login(request, user)
                messages.success(request, "You have been successfully logged in")
                return redirect(reverse("frontend_home"))
            else:
                messages.error(request, "The e-mail password combination does not exist", extra_tags="danger")
        return self.form_invalid(form)
