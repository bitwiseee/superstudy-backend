from django.db import models
from django.contrib.auth.models import User

class Document(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    file = models.FileField(upload_to='documents/')
    text_content = models.TextField(blank=True)
    language = models.CharField(max_length=10, default='en')
    uploaded_at = models.DateTimeField(auto_now_add=True)

class Chat(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    document = models.ForeignKey(Document, on_delete=models.CASCADE)
    question = models.TextField()
    answer = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

class UserProgress(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    points = models.IntegerField(default=0)
    streak = models.IntegerField(default=0)
    documents_uploaded = models.IntegerField(default=0)
    questions_asked = models.IntegerField(default=0)