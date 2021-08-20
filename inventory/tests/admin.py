from django.test import TestCase
from django.contrib.admin.sites import AdminSite
from django.contrib.auth.models import User
from django.urls import reverse
from django.contrib.messages import get_messages
from model_bakery import baker
from inventory.models import Film, Stock


class FilmAdminTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_superuser(
            'admin',
            'test',
            'secret',
        )
        cls.format = 135
        cls.stock = baker.make(
            Stock,
            name='Ektar 100',
            manufacturer__name='Kodak',
        )

    def setUp(self):
        self.client.force_login(user=self.user)

    def test_film_admin_form(self):
        response = self.client.post(reverse('admin:inventory_film_add'), data={
            'format': self.format,
            'stock': self.stock.id,
        }, follow=True)

        messages = [m.message for m in get_messages(response.wsgi_request)]
        film = Film.objects.get(stock=self.stock, format=self.format)
        film_admin_url = reverse('admin:inventory_film_change', args=(film.id,))

        self.assertEqual(response.status_code, 200)
        self.assertIn(
            f'The film “<a href="{film_admin_url}">{self.stock} in 35mm</a>” was added successfully.',
            messages
        )
