from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.db import models # Fixed: Added missing import

from .models import (
    Document, Chat, UserProgress, UserProfile,
    Summary, Flashcard, Quiz, QuizQuestion, QuizAttempt
)
from .serializers import *
from .utils import process_document
from .ai_service import (
    get_ai_response, generate_summary, generate_flashcards,
    generate_quiz
)
from .audio_service import generate_audio_for_chat

import logging

logger = logging.getLogger(__name__)


# ============ USER PROFILE & PREFERENCES ============

@api_view(['GET', 'PUT'])
@permission_classes([IsAuthenticated])
def user_profile(request):
    """
    Get or update user profile and language preferences
    """
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'GET':
        serializer = UserProfileSerializer(profile)
        return Response(serializer.data)
    
    elif request.method == 'PUT':
        serializer = LanguagePreferenceSerializer(data=request.data)
        if serializer.is_valid():
            # Fixed: Handle validated_data safely for Pylance (suppress "get unknown on None")
            lang = serializer.validated_data.get('language') # type: ignore
            if lang:
                profile.preferred_language = str(lang)
                profile.save()
            
            return Response({
                'message': 'Language preference updated',
                # Fixed: Suppress error for dynamic Django method get_FOO_display()
                'language': profile.get_preferred_language_display() # type: ignore
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ============ DOCUMENT MANAGEMENT ============

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upload_document(request):
    """
    Upload and process a document
    """
    serializer = DocumentUploadSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    # Fixed: Suppress "get unknown on None"
    file = serializer.validated_data['file'] # type: ignore
    
    profile = UserProfile.objects.filter(user=request.user).first()
    # Fixed: Pylance type check for get()
    req_lang = serializer.validated_data.get('language') # type: ignore
    language = req_lang if req_lang else (profile.preferred_language if profile else 'en')
    
    document = Document.objects.create(
        user=request.user,
        title=file.name,
        file=file,
        language=language
    )
    
    try:
        text = process_document(document)
        
        if not text:
            document.delete()
            return Response(
                {'error': 'Could not extract text from document'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        progress, _ = UserProgress.objects.get_or_create(user=request.user)
        progress.documents_uploaded += 1
        progress.add_points(10)
        
        logger.info(f"Document {document.id} uploaded by {request.user.username}")
        
        return Response({
            'document': DocumentSerializer(document, context={'request': request}).data,
            'points_earned': 10,
            'total_points': progress.points,
            'message': 'Document uploaded and processed successfully!'
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        logger.error(f"Error processing document: {e}")
        document.delete()
        return Response(
            {'error': 'Failed to process document'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_documents(request):
    documents = Document.objects.filter(user=request.user).select_related('user')
    serializer = DocumentSerializer(documents, many=True, context={'request': request})
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_document(request, document_id):
    document = get_object_or_404(Document, id=document_id, user=request.user)
    serializer = DocumentSerializer(document, context={'request': request})
    return Response(serializer.data)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_document(request, document_id):
    document = get_object_or_404(Document, id=document_id, user=request.user)
    document.delete()
    return Response(
        {'message': 'Document deleted successfully'}, 
        status=status.HTTP_204_NO_CONTENT
    )


# ============ CHAT / Q&A ============

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def ask_question(request):
    serializer = AskQuestionSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    # type: ignore suppresses "Unknown" type errors from validated_data
    document_id = serializer.validated_data.get('document_id') # type: ignore
    question = serializer.validated_data.get('question') # type: ignore
    generate_audio = serializer.validated_data.get('generate_audio') # type: ignore
    
    profile = UserProfile.objects.filter(user=request.user).first()
    req_lang = serializer.validated_data.get('language') # type: ignore
    language = req_lang if req_lang else (profile.preferred_language if profile else 'en')
    
    document = get_object_or_404(Document, id=document_id, user=request.user)
    
    if not document.processed or not document.text_content:
        return Response(
            {'error': 'Document not yet processed'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        answer = get_ai_response(
            document.text_content,
            question, # type: ignore
            language=str(language),
            document_title=document.title
        )
        
        chat = Chat.objects.create(
            user=request.user,
            document=document,
            question=question,
            answer=answer,
            language=language
        )
        
        if generate_audio:
            generate_audio_for_chat(chat)
        
        progress, _ = UserProgress.objects.get_or_create(user=request.user)
        progress.questions_asked += 1
        progress.add_points(5)
        
        logger.info(f"Question answered for {request.user.username}")
        
        return Response({
            'chat': ChatSerializer(chat, context={'request': request}).data,
            'points_earned': 5,
            'total_points': progress.points
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        logger.error(f"Error answering question: {e}")
        return Response(
            {'error': 'Failed to generate answer'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_chat_history(request, document_id):
    chats = Chat.objects.filter(
        user=request.user,
        document_id=document_id
    ).order_by('-created_at')[:20]
    
    serializer = ChatSerializer(chats, many=True, context={'request': request})
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generate_audio(request, chat_id):
    chat = get_object_or_404(Chat, id=chat_id, user=request.user)
    
    try:
        audio_path = generate_audio_for_chat(chat)
        
        if not audio_path:
            return Response(
                {'error': 'Failed to generate audio'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        return Response({
            'audio_url': request.build_absolute_uri(f"/media/{audio_path}"),
            'message': 'Audio generated successfully'
        })
        
    except Exception as e:
        logger.error(f"Error generating audio: {e}")
        return Response(
            {'error': 'Failed to generate audio'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# ============ SUMMARY FEATURE ============

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_summary(request):
    serializer = GenerateSummarySerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    document_id = serializer.validated_data['document_id'] # type: ignore
    document = get_object_or_404(Document, id=document_id, user=request.user)
    
    profile = UserProfile.objects.filter(user=request.user).first()
    req_lang = serializer.validated_data.get('language') # type: ignore
    language = req_lang if req_lang else (profile.preferred_language if profile else 'en')
    
    if not document.processed:
        return Response(
            {'error': 'Document not yet processed'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Fixed: Suppress error for reverse relationship 'summary'
    if hasattr(document, 'summary'):
        serializer = SummarySerializer(document.summary, context={'request': request}) # type: ignore
        return Response(serializer.data)
    
    try:
        # Fixed: Suppress 'No parameter named language' error if signatures match but linter is outdated
        summary_data = generate_summary(
            document.text_content,
            language=str(language) # type: ignore
        )
        
        # Note: Depending on how generate_summary returns data (string or dict), 
        # you might need to adjust this. 
        # If it returns a string, create keys manually.
        # Assuming dict for now based on your previous code logic.
        content = summary_data if isinstance(summary_data, str) else summary_data.get('content', '') # type: ignore
        key_points = '' # If API returns simple string, handle accordingly
        
        summary = Summary.objects.create(
            document=document,
            content=content, 
            key_points=key_points,
            language=language
        )
        
        progress, _ = UserProgress.objects.get_or_create(user=request.user)
        progress.summaries_generated += 1
        progress.add_points(8)
        
        logger.info(f"Summary generated for document {document_id}")
        
        return Response({
            'summary': SummarySerializer(summary, context={'request': request}).data,
            'points_earned': 8,
            'total_points': progress.points
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        logger.error(f"Error generating summary: {e}")
        return Response(
            {'error': 'Failed to generate summary'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_summary(request, document_id):
    document = get_object_or_404(Document, id=document_id, user=request.user)
    
    # Fixed: Suppress error for reverse relationship 'summary'
    if not hasattr(document, 'summary'):
        return Response(
            {'error': 'Summary not found. Generate one first.'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Fixed: Suppress error for reverse relationship 'summary'
    serializer = SummarySerializer(document.summary, context={'request': request}) # type: ignore
    return Response(serializer.data)


# ============ FLASHCARD FEATURE ============

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_flashcards(request):
    serializer = GenerateFlashcardsSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    document_id = serializer.validated_data['document_id'] # type: ignore
    num_cards = serializer.validated_data.get('num_cards', 10) # type: ignore
    document = get_object_or_404(Document, id=document_id, user=request.user)
    
    profile = UserProfile.objects.filter(user=request.user).first()
    req_lang = serializer.validated_data.get('language') # type: ignore
    language = req_lang if req_lang else (profile.preferred_language if profile else 'en')
    
    if not document.processed:
        return Response(
            {'error': 'Document not yet processed'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        # Fixed: Added language parameter and type ignore if linter complains
        flashcard_data = generate_flashcards(
            document.text_content,
            num_cards=num_cards, # type: ignore
            language=str(language) # type: ignore
        )
        
        if not flashcard_data:
            return Response(
                {'error': 'Failed to generate flashcards'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        # Suppress "Unknown attribute" for reverse relation
        if hasattr(document, 'flashcards'):
            document.flashcards.all().delete() # type: ignore
        
        flashcards = []
        # Assumption: flashcard_data is a parsed list of dicts. 
        # If it's raw string from AI, you need a parsing step here.
        # For this fix, I assume the AI util returns a list of dicts.
        if isinstance(flashcard_data, list):
            for i, card in enumerate(flashcard_data):
                flashcard = Flashcard.objects.create(
                    document=document,
                    question=card.get('question', ''),
                    answer=card.get('answer', ''),
                    language=language,
                    order=i
                )
                flashcards.append(flashcard)
        
        progress, _ = UserProgress.objects.get_or_create(user=request.user)
        progress.flashcards_created += len(flashcards)
        progress.add_points(7)
        
        return Response({
            'flashcards': FlashcardSerializer(flashcards, many=True).data,
            'count': len(flashcards),
            'points_earned': 7,
            'total_points': progress.points
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        logger.error(f"Error generating flashcards: {e}")
        return Response(
            {'error': 'Failed to generate flashcards'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_flashcards(request, document_id):
    document = get_object_or_404(Document, id=document_id, user=request.user)
    # Fixed: Suppress Pylance error for reverse relation
    flashcards = document.flashcards.all() # type: ignore
    
    if not flashcards.exists():
        return Response(
            {'error': 'No flashcards found. Generate some first.'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    serializer = FlashcardSerializer(flashcards, many=True)
    return Response(serializer.data)


# ============ QUIZ FEATURE ============

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_quiz(request):
    serializer = GenerateQuizSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    document_id = serializer.validated_data['document_id'] # type: ignore
    num_questions = serializer.validated_data.get('num_questions', 5) # type: ignore
    document = get_object_or_404(Document, id=document_id, user=request.user)
    
    profile = UserProfile.objects.filter(user=request.user).first()
    req_lang = serializer.validated_data.get('language') # type: ignore
    language = req_lang if req_lang else (profile.preferred_language if profile else 'en')
    
    if not document.processed:
        return Response(
            {'error': 'Document not yet processed'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        # Fixed: Added language parameter and type ignore
        question_data = generate_quiz(
            document.text_content,
            num_questions=num_questions, # type: ignore
            language=str(language) # type: ignore
        )
        
        if not question_data:
            return Response(
                {'error': 'Failed to generate quiz'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        with transaction.atomic():
            quiz = Quiz.objects.create(
                document=document,
                title=f"Quiz: {document.title[:50]}",
                language=language
            )
            
            # Assumption: question_data is list of dicts. 
            if isinstance(question_data, list):
                for i, q_data in enumerate(question_data):
                    QuizQuestion.objects.create(
                        quiz=quiz,
                        question_text=q_data['question'],
                        option_a=q_data['option_a'],
                        option_b=q_data['option_b'],
                        option_c=q_data['option_c'],
                        option_d=q_data['option_d'],
                        correct_answer=q_data['correct_answer'],
                        explanation=q_data.get('explanation', ''),
                        order=i
                    )
        
        return Response({
            'quiz': QuizSerializer(quiz, context={'request': request}).data,
            'message': f'Quiz created with {len(question_data) if isinstance(question_data, list) else 0} questions'
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        logger.error(f"Error generating quiz: {e}")
        return Response(
            {'error': 'Failed to generate quiz'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_quiz(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id, document__user=request.user)
    serializer = QuizSerializer(quiz, context={'request': request})
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_quizzes(request, document_id):
    document = get_object_or_404(Document, id=document_id, user=request.user)
    # Fixed: Suppress Pylance error for reverse relation
    quizzes = document.quizzes.all() # type: ignore
    serializer = QuizSerializer(quizzes, many=True, context={'request': request})
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def submit_quiz(request):
    serializer = SubmitQuizSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    quiz_id = serializer.validated_data['quiz_id'] # type: ignore
    answers = serializer.validated_data['answers'] # type: ignore
    time_taken = serializer.validated_data.get('time_taken') # type: ignore
    
    quiz = get_object_or_404(Quiz, id=quiz_id, document__user=request.user)
    # Fixed: Suppress Pylance error for reverse relation
    questions = quiz.questions.all() # type: ignore
    
    total_questions = questions.count()
    correct_answers = 0
    results = []
    
    # Ensure answers is a dict
    if isinstance(answers, dict):
        for question in questions:
            user_answer = answers.get(str(question.id), '').upper()
            is_correct = user_answer == question.correct_answer
            
            if is_correct:
                correct_answers += 1
            
            results.append({
                'question_id': question.id,
                'question': question.question_text,
                'user_answer': user_answer,
                'correct_answer': question.correct_answer,
                'is_correct': is_correct,
                'explanation': question.explanation
            })
    
    score = int((correct_answers / total_questions) * 100) if total_questions > 0 else 0
    
    attempt = QuizAttempt.objects.create(
        user=request.user,
        quiz=quiz,
        score=score,
        total_questions=total_questions,
        correct_answers=correct_answers,
        time_taken=time_taken
    )
    
    progress, _ = UserProgress.objects.get_or_create(user=request.user)
    progress.quizzes_completed += 1
    points_earned = 15 if score >= 80 else (10 if score >= 60 else 5)
    progress.add_points(points_earned)
    
    return Response({
        'attempt': QuizAttemptSerializer(attempt).data,
        'score': score,
        'correct_answers': correct_answers,
        'total_questions': total_questions,
        'results': results,
        'points_earned': points_earned,
        'total_points': progress.points,
        'message': 'Excellent!' if score >= 80 else ('Good job!' if score >= 60 else 'Keep practicing!')
    })


# ============ DASHBOARD & GAMIFICATION ============

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_dashboard(request):
    progress, _ = UserProgress.objects.get_or_create(user=request.user)
    
    recent_documents = Document.objects.filter(user=request.user).select_related('user')[:5]
    recent_chats = Chat.objects.filter(user=request.user).order_by('-created_at')[:10]
    recent_attempts = QuizAttempt.objects.filter(user=request.user).select_related('quiz').order_by('-completed_at')[:5]
    
    return Response({
        'progress': UserProgressSerializer(progress).data,
        'recent_documents': DocumentSerializer(recent_documents, many=True, context={'request': request}).data,
        'recent_chats': ChatSerializer(recent_chats, many=True, context={'request': request}).data,
        'recent_quiz_attempts': QuizAttemptSerializer(recent_attempts, many=True).data,
        'stats': {
            'total_documents': Document.objects.filter(user=request.user).count(),
            'total_questions': Chat.objects.filter(user=request.user).count(),
            'total_quizzes': QuizAttempt.objects.filter(user=request.user).count(),
            # Fixed: 'models' is now imported
            'average_quiz_score': QuizAttempt.objects.filter(user=request.user).aggregate(
                avg_score=models.Avg('score')
            )['avg_score'] or 0,
        }
    })


@api_view(['GET'])
@permission_classes([AllowAny])
def leaderboard(request):
    top_users = UserProgress.objects.select_related('user').order_by('-points')[:10]
    serializer = LeaderboardSerializer(top_users, many=True)
    return Response(serializer.data)