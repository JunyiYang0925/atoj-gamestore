from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.forms import AuthenticationForm
from .models import Player
from .models import Developer
from .models import CustomUser
from .models import Game
from django.core import mail
from django.urls import reverse
import os
from django.contrib.sites.models import Site


class CustomRegistrationForm(UserCreationForm):
    email = forms.EmailField(required = True)
    first_name = forms.CharField(required = False)
    last_name = forms.CharField(required = False)
    is_developer = forms.BooleanField(required = False)

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')

    def save(self, request, commit = True):
        user = super(CustomRegistrationForm, self).save(commit = False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']

        if commit:
            user.save()
        else:
            return None

        if(self.cleaned_data['is_developer']):
            developer = Developer.objects.create(user=user)
            developer.generate_activation_key()

        else:
            player = Player.objects.create(user=user)
            player.generate_activation_key()

        with mail.get_connection() as connection:
            site = request.META['HTTP_HOST']

            full_url = ''.join(['http://', site, reverse('user_activate', args=[user.customuser.activation_key])])
            mail_body = "Your activation key is <b>" + user.customuser.activation_key + "</b>."  + full_url + " or use the link before. "
            mail.EmailMessage("Activation key", mail_body, "noreply@atoj-games.com", (user.email,),
                      connection=connection).send()
        # generating activation key
        user.is_active = False
        user.save()

        print("Actkey: " + user.customuser.activation_key)

        return user

class CustomLoginForm(AuthenticationForm):
    username = forms.CharField(label="Username", max_length=30,
                               widget=forms.TextInput(attrs={'class': 'loginput', 'placeholder': 'Username'}))
    password = forms.CharField(label="Password", max_length=30,
                                widget=forms.PasswordInput(attrs={'class': 'loginput', 'placeholder': 'Password'}))

class GameRegisterForm(forms.ModelForm):
    class Meta:
        model = Game
        fields = ('name', 'url', 'price', 'image')
    #def save(self):
    #    return

class GameEditForm(forms.ModelForm):
    class Meta:
        model = Game
        fields = ('id', 'name', 'url', 'price', 'image')

class RefreshApiKeyForm(forms.Form):
    user_id = forms.IntegerField(required = False)
    api_key = forms.CharField(required = False)

    def save(self, user_id, commit = True):
        try:
            user = Developer.objects.get(user__id=int(user_id))
            user.generate_api_key()
            return True
        except Developer.DoesNotExist:
            return False
