from rest_framework.test import APITestCase

from .models import AuthToken, Member, School


class AuthenticationApiTests(APITestCase):
	def test_register_school_creates_owner_and_returns_token(self):
		response = self.client.post('/api/schools/register/', {
			'schoolName': 'Shuleni Academy',
			'ownerName': 'Amina Otieno',
			'email': 'amina@example.com',
			'username': 'amina',
			'password': 'secret123',
		}, format='json')

		self.assertEqual(response.status_code, 201)
		self.assertEqual(School.objects.count(), 1)
		self.assertEqual(Member.objects.count(), 1)
		self.assertTrue(AuthToken.objects.filter(key=response.data['token']).exists())
		self.assertEqual(response.data['session']['role'], 'owner')

	def test_register_school_rejects_short_password(self):
		response = self.client.post('/api/schools/register/', {
			'schoolName': 'Shuleni Academy',
			'ownerName': 'Amina Otieno',
			'username': 'amina',
			'password': 'short',
		}, format='json')

		self.assertEqual(response.status_code, 400)
		self.assertEqual(School.objects.count(), 0)

	def test_login_session_and_logout(self):
		school = School.objects.create(name='Shuleni Academy')
		owner = Member.objects.create(
			school=school,
			role='owner',
			name='Amina Otieno',
			username='amina',
			password_hash='',
		)
		owner.set_password('secret123')
		owner.save()

		login = self.client.post('/api/auth/login/', {
			'schoolNameOrId': school.id,
			'username': 'amina',
			'password': 'secret123',
		}, format='json')

		self.assertEqual(login.status_code, 200)
		token = login.data['token']
		self.client.credentials(HTTP_AUTHORIZATION=f'Token {token}')

		session = self.client.get('/api/auth/session/')
		self.assertEqual(session.status_code, 200)
		self.assertEqual(session.data['session']['userId'], owner.id)

		logout = self.client.post('/api/auth/logout/')
		self.assertEqual(logout.status_code, 200)
		self.assertFalse(AuthToken.objects.filter(key=token).exists())

		session_after_logout = self.client.get('/api/auth/session/')
		self.assertEqual(session_after_logout.status_code, 401)

	def test_login_rejects_incorrect_password(self):
		school = School.objects.create(name='Shuleni Academy')
		owner = Member.objects.create(
			school=school,
			role='owner',
			name='Amina Otieno',
			username='amina',
			password_hash='',
		)
		owner.set_password('secret123')
		owner.save()

		response = self.client.post('/api/auth/login/', {
			'schoolNameOrId': school.name,
			'username': owner.username,
			'password': 'wrong-password',
		}, format='json')

		self.assertEqual(response.status_code, 400)
		self.assertNotIn('token', response.data)
