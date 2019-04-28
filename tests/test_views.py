from django.contrib.auth.models import User
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from xorgdata.urls import urlpatterns as xorgdata_urlpatterns


class ViewTests(TestCase):
    # Views which are publicy accessible
    PUBLIC_VIEW_IDS = (
        'index',
        'robots',
    )
    # Views which need an authenticated user
    LOGIN_REQUIRED_VIEW_IDS = (
        'admin:index',
        'issues',
    )

    def test_know_all_views(self):
        """Check that every accessible view is either in PUBLIC_VIEW_IDS or in LOGIN_REQUIRED_VIEW_IDS"""
        known_views = set()
        known_views.update(self.PUBLIC_VIEW_IDS)
        known_views.update(self.LOGIN_REQUIRED_VIEW_IDS)
        for urlpattern in xorgdata_urlpatterns:
            try:
                self.assertIn(urlpattern.name, known_views)
                known_views.remove(urlpattern.name)
            except AttributeError:
                pass
        # admin:index is special, because it comes from an inclusion
        known_views.remove('admin:index')

        # Ensure that every view in the local lists exist
        self.assertEqual(set(), known_views, "stray view IDs in tests")

    def test_public_views(self):
        """Test accessing publicy-accessible views"""
        for url_id in self.PUBLIC_VIEW_IDS:
            c = Client()
            resp = c.get(reverse(url_id))
            self.assertEqual(200, resp.status_code)

    def test_login_required_views_forbidden(self):
        """Test accessing login-required views without being logged in"""
        c = Client()
        for url_id in self.LOGIN_REQUIRED_VIEW_IDS:
            resp = c.get(reverse(url_id))
            self.assertEqual(302, resp.status_code,
                             "unexpected HTTP response code for URL %s" % url_id)
            self.assertTrue(resp['Location'].startswith('/admin/login/?'),
                            "unexpected Location header: %r" % resp['Location'])

    def test_login_required_views_success(self):
        """Test accessing login-required views while being logged in"""
        # Create a dummy super user
        User.objects.create_superuser(
            username='superuser',
            email='superuser@localhost.localdomain',
            password='A random insecure password',
        )
        for url_id in self.LOGIN_REQUIRED_VIEW_IDS:
            c = Client()
            self.assertTrue(c.login(username='superuser', password='A random insecure password'))
            resp = c.get(reverse(url_id))
            if resp.status_code == 302:
                self.assertFalse(resp['Location'].startswith(('/accounts/login/?', '/auth-groupex-login?')),
                                 "unexpected login-Location: %r" % resp['Location'])
            elif url_id == 'auth-groupex':
                self.assertEqual(400, resp.status_code,
                                 "unexpected HTTP response code for URL %s" % url_id)
            else:
                self.assertEqual(200, resp.status_code,
                                 "unexpected HTTP response code for URL %s" % url_id)
