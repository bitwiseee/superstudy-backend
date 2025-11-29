from django.test import TestCase
from django.contrib.auth.models import User
from core_app.models import Document, UserProgress, UserProfile

class ModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
    
    def test_user_profile_creation(self):
        """Test that user profile is created"""
        profile = UserProfile.objects.create(
            user=self.user,
            preferred_language='en'
        )
        self.assertEqual(profile.preferred_language, 'en')
    
    def test_user_progress_creation(self):
        """Test that user progress tracks points"""
        progress = UserProgress.objects.create(user=self.user)
        progress.add_points(10)
        self.assertEqual(progress.points, 10)
        self.assertEqual(progress.level, 0)
        
        progress.add_points(50)
        self.assertEqual(progress.level, 1)