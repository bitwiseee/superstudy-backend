"""
API Views with Swagger Documentation
Copy these decorators to your views.py file
"""
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from core_app.serializers import *

# Tag definitions for grouping
TAGS = {
    'profile': 'User Profile',
    'documents': 'Documents',
    'chat': 'Chat & Q&A',
    'summaries': 'Summaries',
    'flashcards': 'Flashcards',
    'quizzes': 'Quizzes',
    'gamification': 'Gamification'
}

# Common response examples
UNAUTHORIZED_RESPONSE = openapi.Response(
    description="Authentication credentials not provided",
    examples={"application/json": {"detail": "Authentication credentials were not provided."}}
)

NOT_FOUND_RESPONSE = openapi.Response(
    description="Resource not found",
    examples={"application/json": {"error": "Not found"}}
)

# User Profile Decorators
user_profile_get = swagger_auto_schema(
    operation_description="Get current user's profile and language preference",
    operation_summary="Get User Profile",
    responses={
        200: UserProfileSerializer,
        401: UNAUTHORIZED_RESPONSE
    },
    tags=['User Profile']
)

user_profile_put = swagger_auto_schema(
    operation_description="Update user's preferred language",
    operation_summary="Update Language Preference",
    request_body=LanguagePreferenceSerializer,
    responses={
        200: openapi.Response(
            description="Language preference updated",
            examples={"application/json": {"message": "Language preference updated", "language": "Yoruba"}}
        )
    },
    tags=['User Profile']
)

# Document Decorators
upload_document_doc = swagger_auto_schema(
    operation_description="Upload a document (PDF, PowerPoint, or Text file) for AI processing",
    operation_summary="Upload Document",
    request_body=DocumentUploadSerializer,
    responses={
        201: openapi.Response(
            description="Document uploaded successfully",
            examples={
                "application/json": {
                    "document": {"id": 1, "title": "textbook.pdf", "processed": True},
                    "points_earned": 10,
                    "total_points": 150
                }
            }
        ),
        400: "Invalid file format or size exceeded"
    },
    tags=['Documents']
)

list_documents_doc = swagger_auto_schema(
    operation_description="List all documents uploaded by the current user",
    operation_summary="List Documents",
    responses={200: DocumentSerializer(many=True)},
    tags=['Documents']
)

# Summary Decorators
create_summary_doc = swagger_auto_schema(
    operation_description="Generate AI-powered summary with key points from document content",
    operation_summary="Generate Summary",
    request_body=GenerateSummarySerializer,
    responses={
        201: openapi.Response(
            description="Summary generated successfully",
            examples={
                "application/json": {
                    "summary": {
                        "content": "This document covers...",
                        "key_points": ["Point 1", "Point 2", "Point 3"]
                    },
                    "points_earned": 8
                }
            }
        ),
        400: "Document not processed or not found"
    },
    tags=['AI Features - Summaries']
)

# Flashcard Decorators
create_flashcards_doc = swagger_auto_schema(
    operation_description="Generate study flashcards from document content",
    operation_summary="Generate Flashcards",
    request_body=GenerateFlashcardsSerializer,
    responses={
        201: openapi.Response(
            description="Flashcards generated successfully",
            examples={
                "application/json": {
                    "flashcards": [
                        {"question": "What is X?", "answer": "X is..."}
                    ],
                    "count": 10,
                    "points_earned": 7
                }
            }
        )
    },
    tags=['AI Features - Flashcards']
)

# Quiz Decorators
create_quiz_doc = swagger_auto_schema(
    operation_description="Generate multiple-choice quiz from document content",
    operation_summary="Generate Quiz",
    request_body=GenerateQuizSerializer,
    responses={
        201: openapi.Response(
            description="Quiz generated successfully",
            examples={
                "application/json": {
                    "quiz": {
                        "id": 1,
                        "title": "Quiz: Document Name",
                        "questions": [
                            {
                                "question_text": "What is X?",
                                "option_a": "Option A",
                                "option_b": "Option B",
                                "option_c": "Option C",
                                "option_d": "Option D",
                                "correct_answer": "B"
                            }
                        ]
                    }
                }
            }
        )
    },
    tags=['AI Features - Quizzes']
)

submit_quiz_doc = swagger_auto_schema(
    operation_description="Submit quiz answers and get score with detailed results",
    operation_summary="Submit Quiz",
    request_body=SubmitQuizSerializer,
    responses={
        200: openapi.Response(
            description="Quiz submitted successfully",
            examples={
                "application/json": {
                    "score": 80,
                    "correct_answers": 4,
                    "total_questions": 5,
                    "points_earned": 15,
                    "message": "Excellent!",
                    "results": [
                        {
                            "question_id": 1,
                            "user_answer": "B",
                            "correct_answer": "B",
                            "is_correct": True
                        }
                    ]
                }
            }
        )
    },
    tags=['AI Features - Quizzes']
)

# Chat Decorators
ask_question_doc = swagger_auto_schema(
    operation_description="Ask a question about document content and get AI-powered answer",
    operation_summary="Ask Question",
    request_body=AskQuestionSerializer,
    responses={
        201: openapi.Response(
            description="Question answered successfully",
            examples={
                "application/json": {
                    "chat": {
                        "question": "What is the main topic?",
                        "answer": "The main topic is...",
                        "audio_url": "http://example.com/audio.mp3"
                    },
                    "points_earned": 5
                }
            }
        )
    },
    tags=['Chat & Q&A']
)

# Dashboard Decorators
dashboard_doc = swagger_auto_schema(
    operation_description="Get user dashboard with stats, progress, and recent activity",
    operation_summary="User Dashboard",
    responses={
        200: openapi.Response(
            description="Dashboard data",
            examples={
                "application/json": {
                    "progress": {
                        "points": 150,
                        "level": 3,
                        "streak": 5,
                        "badges": [{"name": "Scholar", "icon": "📖"}]
                    },
                    "stats": {
                        "total_documents": 5,
                        "total_questions": 20,
                        "average_quiz_score": 85.5
                    }
                }
            }
        )
    },
    tags=['Gamification']
)

leaderboard_doc = swagger_auto_schema(
    operation_description="Get top users leaderboard (public endpoint)",
    operation_summary="Leaderboard",
    responses={
        200: LeaderboardSerializer(many=True)
    },
    tags=['Gamification']
)