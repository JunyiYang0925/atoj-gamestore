from django.test import TestCase, Client
from django.template.loader import render_to_string
from atoj_games.models import Payment, PendingPayment, Game, CustomUser

# 'python manage.py test' runs all test files.

class PaymentTestCase(TestCase):

    def setUp(self):
        pass
