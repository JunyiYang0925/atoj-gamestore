from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from binascii import hexlify
import os

class CustomUser(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, unique=True)
    activation_key = models.CharField(max_length=255, null=True)

    def generate_activation_key(self):
        key = hexlify(os.urandom(25))
        self.activation_key = key.decode()
        self.save()

    def __str__(self):
        return self.user.username

class Player(CustomUser): pass

class Developer(CustomUser):
    api_key = models.CharField(max_length=255, unique=True, null=True)

    def generate_api_key(self):
        key = hexlify(os.urandom(20))
        self.api_key = key.decode()
        self.save()

class Setting(models.Model):
    # name has to be unique
    name = models.CharField(max_length=255, unique=True)
    value = models.CharField(max_length=1000)

    def __str__(self):
        return self.name

class Game(models.Model):
    name = models.CharField(max_length=255, blank=False)
    url = models.CharField(max_length=500, blank=False)
    price = models.DecimalField(max_digits=5, decimal_places=2)
    # related_name because django dislikes having two backwards relations without
    # specifying related_name. Django docs recommended the naming covention.
    developer = models.ForeignKey(Developer, on_delete=models.CASCADE,
                                related_name='%(app_label)s_%(class)s_related')
    bought_by_user = models.ManyToManyField(CustomUser, blank=True)

    # Use pip install Pillow==4.0.0 ## Newer versions didn't seem to work with django
    image = models.ImageField(null=True, blank=True, default = 'default_image.png')

    def __str__(self):
        return self.name

class Payment(models.Model):
    # Payment is not deleted when related game or user is deleted.
    bought_game = models.ForeignKey(Game, on_delete=models.SET_NULL, null=True)
    buyer = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True)
    amount = models.DecimalField(max_digits=5, blank=False,
                                decimal_places=2, null=False)

    # Note that auto_now=True parameter makes DateTimeField hidden when
    # viewed in the Django's admin panel.
    completion_date = models.DateTimeField(auto_now=True)
    payment_app_ref = models.IntegerField(blank=False, null=False)

class PendingPayment(models.Model):
    # Is deleted if related game or user is deleted.
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    buyer = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=5, decimal_places=2,
                                blank=False, null=False)
    creation_date = models.DateTimeField(auto_now=True)


class SaveGame(models.Model):
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    data = models.TextField()

    # Only one save allowed for a game-user pair
    class Meta:
        unique_together = ('game', 'user')

class Highscore(models.Model):
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    score = models.FloatField()

    def __str__(self):
        return self.score
