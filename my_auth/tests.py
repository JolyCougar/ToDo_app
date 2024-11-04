from django.test import TestCase

from django.contrib.auth import get_user_model

from .models import Profile

User = get_user_model()


class ProfileModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpassword')

    def test_profile_creation(self):
        profile = Profile.objects.get(user=self.user)
        self.assertEqual(profile.user.username, 'testuser')
        self.assertEqual(profile.bio, '')
        self.assertFalse(profile.agreement_accepted)
        self.assertFalse(profile.email_verified)
        self.assertFalse(profile.cookies_accepted)
        self.assertEqual(profile.delete_frequency, 'never')

    def test_profile_str(self):
        profile = Profile.objects.get(user=self.user)
        self.assertEqual(str(profile), 'testuser')

    def test_delete_frequency_choices(self):
        profile = Profile.objects.get(user=self.user)
        valid_choices = dict(Profile._meta.get_field('delete_frequency').choices)
        self.assertIn(profile.delete_frequency, valid_choices)

    def test_profile_update(self):
        profile = Profile.objects.get(user=self.user)
        profile.bio = 'Updated bio.'
        profile.save()
        profile.refresh_from_db()
        self.assertEqual(profile.bio, 'Updated bio.')

    def test_profile_avatar_upload_path(self):
        from django.core.files.uploadedfile import SimpleUploadedFile
        profile = Profile.objects.get(user=self.user)
        avatar_file = SimpleUploadedFile("test_avatar.jpg", b"file_content", content_type="image/jpeg")
        profile.avatar = avatar_file
        profile.save()
        expected_path_prefix = f"profile_{profile.pk}/test_avatar"
        self.assertTrue(profile.avatar.name.startswith(expected_path_prefix))

    def test_profile_agreement_default(self):
        new_user = User.objects.create_user(username='newuser', password='newpassword')
        new_profile = Profile.objects.get(user=new_user)
        self.assertFalse(new_profile.agreement_accepted)

    def test_profile_email_verified_default(self):
        new_user = User.objects.create_user(username='anotheruser', password='anotherpassword')
        new_profile = Profile.objects.get(user=new_user)
        self.assertFalse(new_profile.email_verified)

    def test_profile_cookies_accepted_default(self):
        new_user = User.objects.create_user(username='thirduser', password='thirdpassword')
        new_profile = Profile.objects.get(user=new_user)
        self.assertFalse(new_profile.cookies_accepted)

    def test_profile_delete_frequency_default(self):
        new_user = User.objects.create_user(username='fourthuser', password='fourthpassword')
        new_profile = Profile.objects.get(user=new_user)
        self.assertEqual(new_profile.delete_frequency, 'never')



