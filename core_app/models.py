"""
LearnAI Models
Database models for the AI-powered learning platform
"""
from uuid import uuid4
from datetime import timedelta
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator


class UserProfile(models.Model):
    """Extended user profile with language preferences"""
    LANGUAGE_CHOICES = [
        ('en', 'English'),
        ('yo', 'Yoruba'),
        ('ig', 'Igbo'),
        ('ha', 'Hausa'),
    ]
    id = models.UUIDField(default=uuid4, primary_key=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    preferred_language = models.CharField(
        max_length=2, 
        choices=LANGUAGE_CHOICES, 
        default='en',
        help_text='User\'s preferred language for AI responses'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'
    
    def __str__(self):
        lang_display = dict(self.LANGUAGE_CHOICES).get(self.preferred_language, self.preferred_language)
        return f"{self.user.username} - {lang_display}"
    
    def get_language_display(self) -> str:
        """Helper method for IDE type checking"""
        return dict(self.LANGUAGE_CHOICES).get(self.preferred_language, 'English')


class Document(models.Model):
    """Stores uploaded student documents"""
    LANGUAGE_CHOICES = [
        ('en', 'English'),
        ('yo', 'Yoruba'),
        ('ig', 'Igbo'),
        ('ha', 'Hausa'),
    ]
    id = models.UUIDField(default=uuid4, primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='documents')
    title = models.CharField(max_length=255, db_index=True)
    file = models.FileField(upload_to='documents/')
    text_content = models.TextField(blank=True)
    language = models.CharField(
        max_length=2, 
        choices=LANGUAGE_CHOICES, 
        default='en',
        help_text='Language of the document content'
    )
    processed = models.BooleanField(default=False, db_index=True)
    uploaded_at = models.DateTimeField(auto_now_add=True, db_index=True)
    
    class Meta:
        ordering = ['-uploaded_at']
        verbose_name = 'Document'
        verbose_name_plural = 'Documents'
        indexes = [
            models.Index(fields=['-uploaded_at', 'user']),
            models.Index(fields=['processed']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.user.username}"
    
    @property
    def word_count(self):
        """Calculate word count of document"""
        return len(self.text_content.split()) if self.text_content else 0
    
    @property
    def page_count(self):
        """Estimate page count"""
        return max(1, self.text_content.count('--- Page') if self.text_content else 1)


class Summary(models.Model):
    """Stores AI-generated document summaries"""
    document = models.OneToOneField(Document, on_delete=models.CASCADE, related_name='summary')
    content = models.TextField()
    key_points = models.JSONField(default=list, help_text='List of major points from the summary')
    language = models.CharField(max_length=2, default='en')
    generated_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Summary'
        verbose_name_plural = 'Summaries'
        ordering = ['-generated_at']
    
    def __str__(self):
        return f"Summary of {self.document.title}"


class Flashcard(models.Model):
    """Stores flashcards generated from documents"""
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='flashcards')
    question = models.TextField()
    answer = models.TextField()
    language = models.CharField(max_length=2, default='en')
    order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['document', 'order']
        verbose_name = 'Flashcard'
        verbose_name_plural = 'Flashcards'
        indexes = [
            models.Index(fields=['document', 'order']),
        ]
    
    def __str__(self):
        return f"Flashcard {self.order} for {self.document.title}"


class Quiz(models.Model):
    """Stores quizzes generated from documents"""
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='quizzes')
    title = models.CharField(max_length=255)
    language = models.CharField(max_length=2, default='en')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Quiz'
        verbose_name_plural = 'Quizzes'
    
    def __str__(self):
        return f"Quiz: {self.title}"


class QuizQuestion(models.Model):
    """Individual quiz questions"""
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='questions')
    question_text = models.TextField()
    option_a = models.CharField(max_length=500)
    option_b = models.CharField(max_length=500)
    option_c = models.CharField(max_length=500)
    option_d = models.CharField(max_length=500)
    correct_answer = models.CharField(
        max_length=1, 
        choices=[('A', 'A'), ('B', 'B'), ('C', 'C'), ('D', 'D')]
    )
    explanation = models.TextField(blank=True)
    order = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['quiz', 'order']
        verbose_name = 'Quiz Question'
        verbose_name_plural = 'Quiz Questions'
    
    def __str__(self):
        return f"Question {self.order} in {self.quiz.title}"


class QuizAttempt(models.Model):
    """Tracks user quiz attempts"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='quiz_attempts')
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='attempts')
    score = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    total_questions = models.IntegerField()
    correct_answers = models.IntegerField()
    completed_at = models.DateTimeField(auto_now_add=True)
    time_taken = models.DurationField(null=True, blank=True)
    
    class Meta:
        ordering = ['-completed_at']
        verbose_name = 'Quiz Attempt'
        verbose_name_plural = 'Quiz Attempts'
    
    def __str__(self):
        return f"{self.user.username} - {self.quiz.title} - {self.score}%"


class Chat(models.Model):
    """Stores Q&A interactions"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chats')
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='chats')
    question = models.TextField()
    answer = models.TextField()
    language = models.CharField(max_length=2, default='en')
    audio_path = models.CharField(max_length=500, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Chat'
        verbose_name_plural = 'Chats'
        indexes = [
            models.Index(fields=['-created_at', 'user']),
        ]
    
    def __str__(self):
        return f"{self.user.username}: {self.question[:50]}"


class UserProgress(models.Model):
    """Gamification tracking"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='progress')
    points = models.IntegerField(default=0, db_index=True)
    streak = models.IntegerField(default=0)
    last_activity = models.DateField(default=timezone.now)
    documents_uploaded = models.IntegerField(default=0)
    questions_asked = models.IntegerField(default=0)
    quizzes_completed = models.IntegerField(default=0)
    flashcards_created = models.IntegerField(default=0)
    summaries_generated = models.IntegerField(default=0)
    
    class Meta:
        verbose_name = 'User Progress'
        verbose_name_plural = 'User Progress'
    
    def __str__(self):
        return f"{self.user.username} - {self.points} points"
    
    def add_points(self, points_to_add):
        """Add points and update streak"""
        self.points += points_to_add
        today = timezone.now().date()
        
        # Update streak logic
        if self.last_activity == today:
            pass  # Same day, no streak change
        elif self.last_activity == timedelta(days=1):
            self.streak += 1  # Consecutive day
        else:
            self.streak = 1  # Streak broken
        
        self.last_activity = today
        self.save()
    
    @property
    def level(self):
        """Calculate user level based on points"""
        return self.points // 50
    
    @property
    def badges(self):
        """Return earned badges"""
        badges = []
        
        # Upload badges
        if self.documents_uploaded >= 1:
            badges.append({"name": "First Upload", "icon": "📄"})
        if self.documents_uploaded >= 5:
            badges.append({"name": "Document Master", "icon": "📚"})
        if self.documents_uploaded >= 20:
            badges.append({"name": "Library Builder", "icon": "🏛️"})
        
        # Question badges
        if self.questions_asked >= 10:
            badges.append({"name": "Curious Learner", "icon": "🤔"})
        if self.questions_asked >= 50:
            badges.append({"name": "Question Pro", "icon": "❓"})
        if self.questions_asked >= 100:
            badges.append({"name": "Inquisitive Mind", "icon": "🧠"})
        
        # Quiz badges
        if self.quizzes_completed >= 5:
            badges.append({"name": "Quiz Taker", "icon": "📝"})
        if self.quizzes_completed >= 20:
            badges.append({"name": "Quiz Master", "icon": "🎓"})
        if self.quizzes_completed >= 50:
            badges.append({"name": "Test Champion", "icon": "🏆"})
        
        # Points badges
        if self.points >= 100:
            badges.append({"name": "Scholar", "icon": "📖"})
        if self.points >= 500:
            badges.append({"name": "Genius", "icon": "💡"})
        if self.points >= 1000:
            badges.append({"name": "Legend", "icon": "⭐"})
        
        # Streak badges
        if self.streak >= 3:
            badges.append({"name": "Consistent", "icon": "🔥"})
        if self.streak >= 7:
            badges.append({"name": "Week Warrior", "icon": "⚡"})
        if self.streak >= 30:
            badges.append({"name": "Monthly Master", "icon": "🌟"})
        
        # Feature usage badges
        if self.flashcards_created >= 10:
            badges.append({"name": "Flashcard Fan", "icon": "🃏"})
        if self.summaries_generated >= 5:
            badges.append({"name": "Summary Seeker", "icon": "📋"})
        
        return badges