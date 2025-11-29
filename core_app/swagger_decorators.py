"""
Swagger/OpenAPI Decorators for LearnAI API
Copy these decorators to your views.py file before each function
"""
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from core_app.serializers import *


# ============================================
# USER PROFILE & PREFERENCES
# ============================================

user_profile_swagger = {
    'get': swagger_auto_schema(
        operation_description="Get current user's profile including language preference",
        operation_summary="Get User Profile",
        responses={
            200: UserProfileSerializer,
            401: "Authentication required"
        },
        tags=['User Profile']
    ),
    'put': swagger_auto_schema(
        operation_description="Update user's preferred language for AI responses",
        operation_summary="Update Language Preference",
        request_body=LanguagePreferenceSerializer,
        responses={
            200: openapi.Response(
                description="Language updated successfully",
                examples={
                    "application/json": {
                        "message": "Language preference updated",
                        "language": "Yoruba"
                    }
                }
            ),
            400: "Invalid language code"
        },
        tags=['User Profile']
    )
}


# ============================================
# DOCUMENT MANAGEMENT
# ============================================

upload_document_swagger = swagger_auto_schema(
    method='post',
    operation_description="""
    Upload a document (PDF, PowerPoint, or Text file) for AI processing.
    
    **Supported formats:**
    - PDF (.pdf)
    - PowerPoint (.pptx, .ppt)
    - Text (.txt)
    
    **Max file size:** 10MB
    
    **Returns:** Document details with points earned
    """,
    operation_summary="Upload Document",
    manual_parameters=[
        openapi.Parameter(
            'file',
            openapi.IN_FORM,
            description="Document file to upload",
            type=openapi.TYPE_FILE,
            required=True
        ),
        openapi.Parameter(
            'language',
            openapi.IN_FORM,
            description="Document language (en, yo, ig, ha)",
            type=openapi.TYPE_STRING,
            required=False,
            default='en'
        )
    ],
    responses={
        201: openapi.Response(
            description="Document uploaded and processed successfully",
            examples={
                "application/json": {
                    "document": {
                        "id": 1,
                        "title": "Machine_Learning_Textbook.pdf",
                        "file_url": "http://localhost:8000/media/documents/file.pdf",
                        "processed": True,
                        "word_count": 5000,
                        "page_count": 15
                    },
                    "points_earned": 10,
                    "total_points": 150,
                    "message": "Document uploaded and processed successfully!"
                }
            }
        ),
        400: "Invalid file format or size exceeded (max 10MB)"
    },
    tags=['Documents']
)

list_documents_swagger = swagger_auto_schema(
    method='get',
    operation_description="Get list of all documents uploaded by current user",
    operation_summary="List User Documents",
    responses={
        200: DocumentSerializer(many=True),
        401: "Authentication required"
    },
    tags=['Documents']
)

get_document_swagger = swagger_auto_schema(
    method='get',
    operation_description="Get detailed information about a specific document",
    operation_summary="Get Document Details",
    responses={
        200: DocumentSerializer,
        404: "Document not found"
    },
    tags=['Documents']
)

delete_document_swagger = swagger_auto_schema(
    method='delete',
    operation_description="Delete a document and all associated data (summaries, flashcards, quizzes, chats)",
    operation_summary="Delete Document",
    responses={
        204: "Document deleted successfully",
        404: "Document not found"
    },
    tags=['Documents']
)


# ============================================
# CHAT & Q&A
# ============================================

ask_question_swagger = swagger_auto_schema(
    method='post',
    operation_description="""
    Ask a question about document content and receive AI-powered answer.
    
    **Features:**
    - Understands context from document
    - Supports multiple languages
    - Optional audio generation (TTS)
    - Earns 5 points per question
    """,
    operation_summary="Ask Question",
    request_body=AskQuestionSerializer,
    responses={
        201: openapi.Response(
            description="Question answered successfully",
            examples={
                "application/json": {
                    "chat": {
                        "id": 1,
                        "document": 1,
                        "question": "What are the main types of machine learning?",
                        "answer": "Based on the document, the three main types are...",
                        "language": "en",
                        "audio_url": "http://localhost:8000/media/audio/chat_1.mp3"
                    },
                    "points_earned": 5,
                    "total_points": 155
                }
            }
        ),
        400: "Document not processed or invalid request"
    },
    tags=['Chat & Q&A']
)

get_chat_history_swagger = swagger_auto_schema(
    method='get',
    operation_description="Get chat history for a specific document (last 20 messages)",
    operation_summary="Get Chat History",
    responses={
        200: ChatSerializer(many=True),
        404: "Document not found"
    },
    tags=['Chat & Q&A']
)

generate_audio_swagger = swagger_auto_schema(
    method='post',
    operation_description="Generate audio (text-to-speech) for an existing chat message",
    operation_summary="Generate Audio for Chat",
    responses={
        200: openapi.Response(
            description="Audio generated successfully",
            examples={
                "application/json": {
                    "audio_url": "http://localhost:8000/media/audio/chat_1.mp3",
                    "message": "Audio generated successfully"
                }
            }
        ),
        404: "Chat not found"
    },
    tags=['Chat & Q&A']
)


# ============================================
# SUMMARY FEATURE
# ============================================

create_summary_swagger = swagger_auto_schema(
    method='post',
    operation_description="""
    Generate AI-powered comprehensive summary with key points.
    
    **Returns:**
    - Detailed summary (3-5 paragraphs)
    - 5-7 key points extracted
    - 8 points earned
    
    **Note:** Summary is cached - regenerating returns existing summary
    """,
    operation_summary="Generate Summary",
    request_body=GenerateSummarySerializer,
    responses={
        201: openapi.Response(
            description="Summary generated successfully",
            examples={
                "application/json": {
                    "summary": {
                        "id": 1,
                        "document": 1,
                        "content": "This document provides a comprehensive introduction to machine learning...",
                        "key_points": [
                            "Machine learning is a subset of AI",
                            "Three main types: supervised, unsupervised, reinforcement",
                            "Training data is crucial for model performance",
                            "Applications include image recognition and NLP",
                            "Overfitting is a common challenge"
                        ],
                        "language": "en"
                    },
                    "points_earned": 8,
                    "total_points": 163
                }
            }
        ),
        400: "Document not processed"
    },
    tags=['AI Features - Summaries']
)

get_summary_swagger = swagger_auto_schema(
    method='get',
    operation_description="Retrieve existing summary for a document",
    operation_summary="Get Summary",
    responses={
        200: SummarySerializer,
        404: "Summary not found - generate one first"
    },
    tags=['AI Features - Summaries']
)


# ============================================
# FLASHCARD FEATURE
# ============================================

create_flashcards_swagger = swagger_auto_schema(
    method='post',
    operation_description="""
    Generate study flashcards from document content.
    
    **Parameters:**
    - num_cards: 3-20 cards (default: 10)
    - language: Response language
    
    **Returns:**
    - Question-answer pairs
    - Educational content
    - 7 points earned
    
    **Note:** Regenerating replaces old flashcards
    """,
    operation_summary="Generate Flashcards",
    request_body=GenerateFlashcardsSerializer,
    responses={
        201: openapi.Response(
            description="Flashcards generated successfully",
            examples={
                "application/json": {
                    "flashcards": [
                        {
                            "id": 1,
                            "question": "What is supervised learning?",
                            "answer": "Supervised learning is a type of machine learning that uses labeled training data...",
                            "order": 0
                        },
                        {
                            "id": 2,
                            "question": "What is overfitting?",
                            "answer": "Overfitting occurs when a model performs well on training data but poorly on new data...",
                            "order": 1
                        }
                    ],
                    "count": 10,
                    "points_earned": 7,
                    "total_points": 170
                }
            }
        ),
        400: "Document not processed or invalid parameters"
    },
    tags=['AI Features - Flashcards']
)

get_flashcards_swagger = swagger_auto_schema(
    method='get',
    operation_description="Retrieve all flashcards for a document",
    operation_summary="Get Flashcards",
    responses={
        200: FlashcardSerializer(many=True),
        404: "No flashcards found - generate some first"
    },
    tags=['AI Features - Flashcards']
)


# ============================================
# QUIZ FEATURE
# ============================================

create_quiz_swagger = swagger_auto_schema(
    method='post',
    operation_description="""
    Generate multiple-choice quiz from document content.
    
    **Parameters:**
    - num_questions: 3-15 questions (default: 5)
    - language: Quiz language
    
    **Each question includes:**
    - Question text
    - 4 options (A, B, C, D)
    - Correct answer
    - Explanation
    """,
    operation_summary="Generate Quiz",
    request_body=GenerateQuizSerializer,
    responses={
        201: openapi.Response(
            description="Quiz generated successfully",
            examples={
                "application/json": {
                    "quiz": {
                        "id": 1,
                        "title": "Quiz: Machine Learning Textbook",
                        "questions": [
                            {
                                "id": 1,
                                "question_text": "Which type of machine learning uses labeled data?",
                                "option_a": "Unsupervised learning",
                                "option_b": "Supervised learning",
                                "option_c": "Reinforcement learning",
                                "option_d": "Deep learning",
                                "correct_answer": "B",
                                "explanation": "Supervised learning uses labeled data where correct outputs are known."
                            }
                        ],
                        "question_count": 5
                    },
                    "message": "Quiz created with 5 questions"
                }
            }
        ),
        400: "Document not processed or invalid parameters"
    },
    tags=['AI Features - Quizzes']
)

get_quiz_swagger = swagger_auto_schema(
    method='get',
    operation_description="Get quiz details including all questions",
    operation_summary="Get Quiz",
    responses={
        200: QuizSerializer,
        404: "Quiz not found"
    },
    tags=['AI Features - Quizzes']
)

list_quizzes_swagger = swagger_auto_schema(
    method='get',
    operation_description="List all quizzes created for a document",
    operation_summary="List Document Quizzes",
    responses={
        200: QuizSerializer(many=True),
        404: "Document not found"
    },
    tags=['AI Features - Quizzes']
)

submit_quiz_swagger = swagger_auto_schema(
    method='post',
    operation_description="""
    Submit quiz answers and receive detailed results.
    
    **Scoring:**
    - 80%+ score: 15 points + "Excellent!"
    - 60-79% score: 10 points + "Good job!"
    - <60% score: 5 points + "Keep practicing!"
    
    **Returns:**
    - Overall score
    - Correct/incorrect for each question
    - Explanations
    - Points earned
    """,
    operation_summary="Submit Quiz",
    request_body=SubmitQuizSerializer,
    responses={
        200: openapi.Response(
            description="Quiz submitted successfully",
            examples={
                "application/json": {
                    "attempt": {
                        "id": 1,
                        "score": 80,
                        "correct_answers": 4,
                        "total_questions": 5
                    },
                    "score": 80,
                    "results": [
                        {
                            "question_id": 1,
                            "question": "Which type uses labeled data?",
                            "user_answer": "B",
                            "correct_answer": "B",
                            "is_correct": True,
                            "explanation": "Supervised learning uses labeled data..."
                        }
                    ],
                    "points_earned": 15,
                    "total_points": 185,
                    "message": "Excellent!"
                }
            }
        ),
        400: "Invalid quiz or answers"
    },
    tags=['AI Features - Quizzes']
)


# ============================================
# DASHBOARD & GAMIFICATION
# ============================================

user_dashboard_swagger = swagger_auto_schema(
    method='get',
    operation_description="""
    Get comprehensive user dashboard with stats and progress.
    
    **Includes:**
    - Points, level, streak
    - Earned badges
    - Recent documents
    - Recent chats
    - Recent quiz attempts
    - Overall statistics
    """,
    operation_summary="User Dashboard",
    responses={
        200: openapi.Response(
            description="Dashboard data",
            examples={
                "application/json": {
                    "progress": {
                        "username": "john_doe",
                        "points": 185,
                        "level": 3,
                        "streak": 5,
                        "documents_uploaded": 3,
                        "questions_asked": 15,
                        "quizzes_completed": 2,
                        "flashcards_created": 20,
                        "summaries_generated": 3,
                        "badges": [
                            {"name": "First Upload", "icon": "📄"},
                            {"name": "Curious Learner", "icon": "🤔"},
                            {"name": "Scholar", "icon": "📖"}
                        ]
                    },
                    "stats": {
                        "total_documents": 3,
                        "total_questions": 15,
                        "total_quizzes": 2,
                        "average_quiz_score": 82.5
                    }
                }
            }
        ),
        401: "Authentication required"
    },
    tags=['Gamification']
)

leaderboard_swagger = swagger_auto_schema(
    method='get',
    operation_description="""
    Get top 10 users leaderboard (public endpoint).
    
    **Sorted by:** Total points (highest first)
    
    **Note:** No authentication required
    """,
    operation_summary="Leaderboard",
    responses={
        200: openapi.Response(
            description="Top users leaderboard",
            examples={
                "application/json": [
                    {
                        "username": "top_student",
                        "points": 1250,
                        "level": 25,
                        "streak": 30,
                        "badge_count": 15
                    },
                    {
                        "username": "john_doe",
                        "points": 185,
                        "level": 3,
                        "streak": 5,
                        "badge_count": 4
                    }
                ]
            }
        )
    },
    tags=['Gamification']
)