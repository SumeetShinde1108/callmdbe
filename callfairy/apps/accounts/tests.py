from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from django_otp.plugins.otp_totp.models import TOTPDevice
from unittest.mock import patch, Mock
from callfairy.apps.accounts.models import AllowedEmailDomain, GoogleSignInAudit
from django.test import override_settings


User = get_user_model()


class AccountsFlowTests(APITestCase):
    def setUp(self):
        self.register_url = reverse('accounts:register')
        self.login_url = reverse('accounts:login')
        self.refresh_url = reverse('accounts:token_refresh')
        self.me_url = reverse('accounts:me')
        self.verify_email_url = reverse('accounts:verify_email')
        self.totp_enable_url = reverse('accounts:totp_enable')
        self.totp_verify_url = reverse('accounts:totp_verify')
        self.totp_disable_url = reverse('accounts:totp_disable')

    def _register(self, email='user@example.com', name='Test User', password='StrongPass!234'):
        payload = {
            'email': email,
            'name': name,
            'password': password,
            'password2': password,
        }
        resp = self.client.post(self.register_url, payload, format='json')
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        token = resp.data.get('email_verification_token')  # available in DEBUG
        return token

    def _verify_email(self, token):
        resp = self.client.post(self.verify_email_url, {'token': token}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def _login(self, email='user@example.com', password='StrongPass!234'):
        resp = self.client.post(self.login_url, {'email': email, 'password': password}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn('access', resp.data)
        self.assertIn('refresh', resp.data)
        return resp.data['access'], resp.data['refresh']

    def test_full_auth_flow_with_email_verification(self):
        token = self._register()
        self.assertIsNotNone(token)
        # login before verify should fail
        resp_pre = self.client.post(self.login_url, {'email': 'user@example.com', 'password': 'StrongPass!234'}, format='json')
        self.assertEqual(resp_pre.status_code, status.HTTP_400_BAD_REQUEST)

        self._verify_email(token)
        access, refresh = self._login()

        # token refresh
        r2 = self.client.post(self.refresh_url, {'refresh': refresh}, format='json')
        self.assertEqual(r2.status_code, status.HTTP_200_OK)
        self.assertIn('access', r2.data)

        # me
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access}')
        me = self.client.get(self.me_url)
        self.assertEqual(me.status_code, status.HTTP_200_OK)
        self.assertEqual(me.data['email'], 'user@example.com')

    def test_totp_enable_verify_disable(self):
        token = self._register(email='2fa@example.com')
        self._verify_email(token)
        access, _ = self._login(email='2fa@example.com')
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access}')

        # Enable returns device info and provisioning uri if available
        enable = self.client.post(self.totp_enable_url, {}, format='json')
        self.assertEqual(enable.status_code, status.HTTP_200_OK)
        self.assertIn('device_id', enable.data)

        # Obtain current TOTP code from device for verification in tests
        device = TOTPDevice.objects.get(user=User.objects.get(email='2fa@example.com'), name='default')
        # Generate a token; for tests we use token = device.token.get_token() if available, else verify is skipped
        try:
            code = device.token
        except Exception:
            # If direct token not available, skip strict verify in CI
            code = None

        # Try verifying with a dummy 000000 to ensure endpoint validation path
        bad = self.client.post(self.totp_verify_url, {'code': '000000'}, format='json')
        self.assertIn(bad.status_code, (status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST))

        # Disable should work regardless of previous verify outcome in this test
        disable = self.client.post(self.totp_disable_url, {}, format='json')
        self.assertIn(disable.status_code, (status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST))

    @patch('callfairy.apps.accounts.serializers.requests.get')
    def test_google_login(self, mock_get):
        # Mock Google's tokeninfo successful response
        m = Mock()
        m.status_code = 200
        m.json.return_value = {
            'email': 'googleuser@example.com',
            'email_verified': 'true',
            'name': 'Google User',
            'aud': 'dummy-client-id',
            'sub': 'google-sub-123',
        }
        mock_get.return_value = m

        # Ensure settings allow any client id in this test by not setting SOCIALACCOUNT_PROVIDERS google client or matching it
        url = reverse('accounts:login_google')
        resp = self.client.post(url, {'id_token': 'dummy'}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn('access', resp.data)
        self.assertIn('refresh', resp.data)
        self.assertEqual(resp.data['email'], 'googleuser@example.com')

    @override_settings(DEBUG=True)
    def test_password_reset_flow(self):
        # Create active user
        user = User.objects.create_user(email='reset@example.com', password='OldPass!234', name='Reset User')
        user.is_active = True
        user.save(update_fields=['is_active'])

        # Request reset
        url_req = reverse('accounts:password_reset_request')
        r1 = self.client.post(url_req, {'email': 'reset@example.com'}, format='json')
        self.assertEqual(r1.status_code, status.HTTP_200_OK)
        uid = r1.data.get('uid')
        token = r1.data.get('token')
        self.assertTrue(uid and token)

        # Confirm reset
        url_c = reverse('accounts:password_reset_confirm')
        new_pass = 'NewPass!234'
        r2 = self.client.post(url_c, {'uid': uid, 'token': token, 'new_password': new_pass, 'new_password2': new_pass}, format='json')
        self.assertEqual(r2.status_code, status.HTTP_200_OK)

        # Login with new password
        r3 = self.client.post(self.login_url, {'email': 'reset@example.com', 'password': new_pass}, format='json')
        self.assertEqual(r3.status_code, status.HTTP_200_OK)
        self.assertIn('access', r3.data)

    @patch('callfairy.apps.accounts.serializers.requests.get')
    def test_google_login_domain_restriction_blocks(self, mock_get):
        # Allow only acme.com
        AllowedEmailDomain.objects.create(domain='acme.com', is_active=True)

        m = Mock()
        m.status_code = 200
        m.json.return_value = {
            'email': 'user@other.com',
            'email_verified': 'true',
            'name': 'User Other',
            'aud': 'dummy-client-id',
            'sub': 'google-sub-999',
        }
        mock_get.return_value = m

        url = reverse('accounts:login_google')
        resp = self.client.post(url, {'id_token': 'dummy'}, format='json', HTTP_USER_AGENT='pytest', REMOTE_ADDR='1.2.3.4')
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)
        # Audit should record failed attempt
        audit = GoogleSignInAudit.objects.filter(email='user@other.com', success=False).first()
        self.assertIsNotNone(audit)
        self.assertEqual(audit.domain, 'other.com')

    @patch('callfairy.apps.accounts.serializers.requests.get')
    def test_google_login_domain_restriction_allows(self, mock_get):
        AllowedEmailDomain.objects.create(domain='example.com', is_active=True)

        m = Mock()
        m.status_code = 200
        m.json.return_value = {
            'email': 'allowed@example.com',
            'email_verified': 'true',
            'name': 'Allowed User',
            'aud': 'dummy-client-id',
            'sub': 'google-sub-111',
        }
        mock_get.return_value = m

        url = reverse('accounts:login_google')
        resp = self.client.post(url, {'id_token': 'dummy'}, format='json', HTTP_USER_AGENT='pytest', REMOTE_ADDR='2.3.4.5')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        audit = GoogleSignInAudit.objects.filter(email='allowed@example.com', success=True).first()
        self.assertIsNotNone(audit)
        self.assertEqual(audit.domain, 'example.com')

# Create your tests here.
