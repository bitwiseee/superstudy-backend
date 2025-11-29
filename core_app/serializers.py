#API Serializers for LearnAI
#Handles data serialization and validation

from rest_framework import serializers
from django.contrib.auth.models import User
from core_app.models import (
    Document, Chat, UserProgress, UserProfile,
    Summary, Flashcard, Quiz, QuizQuestion, QuizAttempt
)


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for user profile with language preferences"""
    username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta: #type:ignore
        model = UserProfile
        fields = ['id', 'username', 'preferred_language', 'created_at']
        read_only_fields = ['created_at']


class DocumentSerializer(serializers.ModelSerializer):
    """Serializer for Document model"""
    file_url = serializers.SerializerMethodField()
    file_size = serializers.SerializerMethodField()
    word_count = serializers.IntegerField(read_only=True)
    page_count = serializers.IntegerField(read_only=True)
    has_summary = serializers.SerializerMethodField()
    flashcard_count = serializers.SerializerMethodField()
    quiz_count = serializers.SerializerMethodField()
    
    class Meta: #type:ignore
        model = Document
        fields = [
            'id', 'title', 'file', 'file_url', 'file_size',
            'language', 'processed', 'uploaded_at', 'word_count',
            'page_count', 'has_summary', 'flashcard_count', 'quiz_count'
        ]
        read_only_fields = ['processed', 'uploaded_at', 'word_count', 'page_count']
    
    def get_file_url(self, obj):
        if obj.file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.file.url)
        return None
    
    def get_file_size(self, obj):
        if obj.file:
            return obj.file.size
        return None
    
    def get_has_summary(self, obj):
        return hasattr(obj, 'summary')
    
    def get_flashcard_count(self, obj):
        return obj.flashcards.count()
    
    def get_quiz_count(self, obj):
        return obj.quizzes.count()


class DocumentUploadSerializer(serializers.Serializer):
    """Serializer for document upload"""
    file = serializers.FileField()
    language = serializers.ChoiceField(
        choices=['en', 'yo', 'ig', 'ha'],
        default='en',
        required=False
    )
    
    def validate_file(self, value):
        # Check file extension
        allowed_extensions = ['.pdf', '.pptx', '.ppt', '.txt']
        ext = value.name.lower().split('.')[-1]
        if f'.{ext}' not in allowed_extensions:
            raise serializers.ValidationError(
                f"Unsupported file type. Allowed: {', '.join(allowed_extensions)}"
            )
        
        # Check file size (max 10MB for hackathon)
        max_size = 10 * 1024 * 1024  # 10MB
        if value.size > max_size:
            raise serializers.ValidationError(
                "File size too large. Maximum size is 10MB."
            )
        
        return value


class SummarySerializer(serializers.ModelSerializer):
    """Serializer for document summaries"""
    document_title = serializers.CharField(source='document.title', read_only=True)
    
    class Meta: #type:ignore
        model = Summary
        fields = ['id', 'document', 'document_title', 'content', 'key_points', 'language', 'generated_at']
        read_only_fields = ['generated_at']


class FlashcardSerializer(serializers.ModelSerializer):
    """Serializer for flashcards"""
    class Meta: #type:ignore
        model = Flashcard
        fields = ['id', 'document', 'question', 'answer', 'language', 'order', 'created_at']
        read_only_fields = ['created_at']


class QuizQuestionSerializer(serializers.ModelSerializer):
    """Serializer for quiz questions"""
    class Meta: #type:ignore
        model = QuizQuestion
        fields = [
            'id', 'question_text', 'option_a', 'option_b', 
            'option_c', 'option_d', 'correct_answer', 
            'explanation', 'order'
        ]


class QuizSerializer(serializers.ModelSerializer):
    """Serializer for quizzes"""
    questions = QuizQuestionSerializer(many=True, read_only=True)
    document_title = serializers.CharField(source='document.title', read_only=True)
    question_count = serializers.SerializerMethodField()
    
    class Meta: #type:ignore
        model = Quiz
        fields = ['id', 'document', 'document_title', 'title', 'language', 'questions', 'question_count', 'created_at']
        read_only_fields = ['created_at']
    
    def get_question_count(self, obj):
        return obj.questions.count()


class QuizAttemptSerializer(serializers.ModelSerializer):
    """Serializer for quiz attempts"""
    quiz_title = serializers.CharField(source='quiz.title', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta: #type:ignore
        model = QuizAttempt
        fields = [
            'id', 'user', 'username', 'quiz', 'quiz_title',
            'score', 'total_questions', 'correct_answers',
            'completed_at', 'time_taken'
        ]
        read_only_fields = ['completed_at']


class SubmitQuizSerializer(serializers.Serializer):
    """Serializer for submitting quiz answers"""
    quiz_id = serializers.IntegerField()
    answers = serializers.DictField(
        child=serializers.CharField(),
        help_text="Dict mapping question IDs to answer letters (A/B/C/D)"
    )
    time_taken = serializers.DurationField(required=False)


class ChatSerializer(serializers.ModelSerializer):
    """Serializer for Chat model"""
    audio_url = serializers.SerializerMethodField()
    document_title = serializers.CharField(source='document.title', read_only=True)
    
    class Meta: #type:ignore
        model = Chat
        fields = [
            'id', 'document', 'document_title', 'question', 
            'answer', 'language', 'audio_path', 'audio_url', 'created_at'
        ]
        read_only_fields = ['answer', 'audio_path', 'created_at']
    
    def get_audio_url(self, obj):
        if obj.audio_path:
            request = self.context.get('request')
            if request:
                from django.conf import settings
                return request.build_absolute_uri(f"{settings.MEDIA_URL}{obj.audio_path}")
        return None


class AskQuestionSerializer(serializers.Serializer):
    """Serializer for asking questions"""
    document_id = serializers.IntegerField()
    question = serializers.CharField(max_length=1000)
    language = serializers.ChoiceField(
        choices=['en', 'yo', 'ig', 'ha'],
        required=False
    )
    generate_audio = serializers.BooleanField(default=False)
    
    def validate_question(self, value):
        if len(value.strip()) < 3:
            raise serializers.ValidationError(
                "Question must be at least 3 characters long."
            )
        return value


class GenerateSummarySerializer(serializers.Serializer):
    """Serializer for generating summaries"""
    document_id = serializers.IntegerField()
    language = serializers.ChoiceField(
        choices=['en', 'yo', 'ig', 'ha'],
        required=False
    )


class GenerateFlashcardsSerializer(serializers.Serializer):
    """Serializer for generating flashcards"""
    document_id = serializers.IntegerField()
    language = serializers.ChoiceField(
        choices=['en', 'yo', 'ig', 'ha'],
        required=False
    )
    num_cards = serializers.IntegerField(default=10, min_value=3, max_value=20)


class GenerateQuizSerializer(serializers.Serializer):
    """Serializer for generating quizzes"""
    document_id = serializers.IntegerField()
    language = serializers.ChoiceField(
        choices=['en', 'yo', 'ig', 'ha'],
        required=False
    )
    num_questions = serializers.IntegerField(default=5, min_value=3, max_value=15)


class UserProgressSerializer(serializers.ModelSerializer):
    """Serializer for UserProgress model"""
    level = serializers.IntegerField(read_only=True)
    badges = serializers.JSONField(read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta: #type:ignore
        model = UserProgress
        fields = [
            'username', 'points', 'level', 'streak', 
            'documents_uploaded', 'questions_asked', 
            'quizzes_completed', 'flashcards_created',
            'summaries_generated', 'badges', 'last_activity'
        ]
        read_only_fields = [
            'points', 'streak', 'documents_uploaded', 
            'questions_asked', 'quizzes_completed',
            'flashcards_created', 'summaries_generated', 'last_activity'
        ]


class LeaderboardSerializer(serializers.ModelSerializer):
    """Serializer for leaderboard"""
    username = serializers.CharField(source='user.username')
    level = serializers.IntegerField()
    badge_count = serializers.SerializerMethodField()
    
    class Meta: #type:ignore
        model = UserProgress
        fields = ['username', 'points', 'level', 'streak', 'badge_count']
    
    def get_badge_count(self, obj):
        return len(obj.badges)


class LanguagePreferenceSerializer(serializers.Serializer):
    """Serializer for updating language preference"""
    language = serializers.ChoiceField(
        choices=['en', 'yo', 'ig', 'ha']
    )