#URL Configuration for LearnAI API
#All API endpoints with new features

from django.urls import path
from . import views

urlpatterns = [
    # User Profile & Preferences
    path('profile/', views.user_profile, name='user-profile'),
    
    # Document Management
    path('upload/', views.upload_document, name='upload-document'),
    path('documents/', views.list_documents, name='list-documents'),
    path('documents/<int:document_id>/', views.get_document, name='get-document'),
    path('documents/<int:document_id>/delete/', views.delete_document, name='delete-document'),
    
    # Chat / Q&A
    path('chat/ask/', views.ask_question, name='ask-question'),
    path('chat/history/<int:document_id>/', views.get_chat_history, name='chat-history'),
    path('chat/<int:chat_id>/audio/', views.generate_audio, name='generate-audio'),
    
    # Summary Feature
    path('summaries/generate/', views.create_summary, name='create-summary'),
    path('summaries/<int:document_id>/', views.get_summary, name='get-summary'),
    
    # Flashcards Feature
    path('flashcards/generate/', views.create_flashcards, name='create-flashcards'),
    path('flashcards/<int:document_id>/', views.get_flashcards, name='get-flashcards'),
    
    # Quiz Feature
    path('quizzes/generate/', views.create_quiz, name='create-quiz'),
    path('quizzes/<int:quiz_id>/', views.get_quiz, name='get-quiz'),
    path('quizzes/document/<int:document_id>/', views.list_quizzes, name='list-quizzes'),
    path('quizzes/submit/', views.submit_quiz, name='submit-quiz'),
    
    # Dashboard & Gamification
    path('dashboard/', views.user_dashboard, name='user-dashboard'),
    path('leaderboard/', views.leaderboard, name='leaderboard'),
]