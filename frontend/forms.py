from django.utils.translation import ugettext_lazy as _
from django import forms

class LoginForm(forms.Form):
    email = forms.EmailField(widget=forms.TextInput(attrs={'placeholder': 'Email Address',
                                                            'class': 'required form-control',
                                                            "maxlength": 75},
                                                               ),
                             label=_("Email address"))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': 'Password',
                                                          'class': 'required form-control'},
                                                          render_value=False),
                                label=_("Password"))
