from django.contrib import admin
from .models import (
    UserProfile, Document, Summary, Flashcard, 
    Quiz, QuizQuestion, QuizAttempt, Chat, UserProgress
)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'preferred_language', 'created_at']
    list_filter = ['preferred_language', 'created_at']
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ['title', 'user', 'language', 'processed', 'word_count', 'uploaded_at']
    list_filter = ['processed', 'language', 'uploaded_at']
    search_fields = ['title', 'user__username']
    readonly_fields = ['uploaded_at', 'word_count', 'page_count']
    date_hierarchy = 'uploaded_at'


@admin.register(Summary)
class SummaryAdmin(admin.ModelAdmin):
    list_display = ['document', 'language', 'generated_at']
    list_filter = ['language', 'generated_at']
    search_fields = ['document__title', 'content']
    readonly_fields = ['generated_at']
    date_hierarchy = 'generated_at'


@admin.register(Flashcard)
class FlashcardAdmin(admin.ModelAdmin):
    list_display = ['document', 'order', 'language', 'created_at']
    list_filter = ['language', 'created_at']
    search_fields = ['document__title', 'question', 'answer']
    readonly_fields = ['created_at']
    ordering = ['document', 'order']


class QuizQuestionInline(admin.TabularInline):
    model = QuizQuestion
    extra = 0
    fields = ['order', 'question_text', 'correct_answer']
    readonly_fields = ['order']


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ['title', 'document', 'language', 'question_count', 'created_at']
    list_filter = ['language', 'created_at']
    search_fields = ['title', 'document__title']
    readonly_fields = ['created_at']
    inlines = [QuizQuestionInline]
    date_hierarchy = 'created_at'
    
    def question_count(self, obj):
        return obj.questions.count()
    question_count.short_description = 'Questions'


@admin.register(QuizQuestion)
class QuizQuestionAdmin(admin.ModelAdmin):
    list_display = ['quiz', 'order', 'question_text', 'correct_answer']
    list_filter = ['quiz__language', 'correct_answer']
    search_fields = ['question_text', 'quiz__title']
    ordering = ['quiz', 'order']


@admin.register(QuizAttempt)
class QuizAttemptAdmin(admin.ModelAdmin):
    list_display = ['user', 'quiz', 'score', 'correct_answers', 'total_questions', 'completed_at']
    list_filter = ['completed_at', 'score']
    search_fields = ['user__username', 'quiz__title']
    readonly_fields = ['completed_at']
    date_hierarchy = 'completed_at'


@admin.register(Chat)
class ChatAdmin(admin.ModelAdmin):
    list_display = ['user', 'document', 'question', 'language', 'created_at']
    list_filter = ['language', 'created_at']
    search_fields = ['question', 'answer', 'user__username', 'document__title']
    readonly_fields = ['created_at']
    date_hierarchy = 'created_at'


@admin.register(UserProgress)
class UserProgressAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'points', 'level', 'streak', 
        'documents_uploaded', 'questions_asked',
        'quizzes_completed', 'last_activity'
    ]
    list_filter = ['last_activity']
    search_fields = ['user__username']
    readonly_fields = ['level', 'badges']
    
    fieldsets = (
        ('User', {
            'fields': ('user',)
        }),
        ('Points & Level', {
            'fields': ('points', 'level', 'streak', 'last_activity')
        }),
        ('Activity Stats', {
            'fields': (
                'documents_uploaded', 'questions_asked',
                'quizzes_completed', 'flashcards_created',
                'summaries_generated'
            )
        }),
        ('Achievements', {
            'fields': ('badges',)
        }),
    )