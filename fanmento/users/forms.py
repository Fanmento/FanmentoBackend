from django import forms
from django.contrib.localflavor.us.forms import USPhoneNumberField

from bootstrap.forms import BootstrapForm, Fieldset

class CreateUserForm(BootstrapForm):
    email          = forms.CharField(max_length=75)
    password       = forms.CharField(widget=forms.PasswordInput(), max_length=100, required=False)
    facebook_token = forms.CharField(required=False)
    name           = forms.CharField(required=False)

class RegistrationResourceForm(BootstrapForm):
    class Meta:
        layout = (
            Fieldset("Update a user", "name", "email", "password", "admin"),
        )

    name     = forms.CharField(max_length=75, required=False)
    email    = forms.CharField(max_length=75)
    password = forms.CharField(widget=forms.PasswordInput(), max_length=100, required=False)
    admin    = forms.BooleanField(required=False)

class ResetPasswordForm(BootstrapForm):
    password = forms.CharField(max_length=100, label="Password")
    confirm = forms.CharField(max_length=100, label="Confirm")
    token = forms.CharField(max_length=100)

class RequestResetPasswordForm(BootstrapForm):
    email = forms.CharField(max_length=100, label="Email")

class UserImageForm(forms.Form):
    #image          = forms.FileField(required=True)
    background_url   = forms.CharField(required=False)
    twitter_message  = forms.CharField(widget=forms.Textarea, required=False)
    facebook_message = forms.CharField(widget=forms.Textarea, required=False)
    email_message    = forms.CharField(widget=forms.Textarea, required=False)
    client_name      = forms.CharField(max_length=75, required=False) 

class ImageDeleteForm(forms.Form):
    user_id  = forms.IntegerField(required=True)
    image_id = forms.IntegerField(required=True)
