from random import choices
from tkinter import CASCADE
from django.db import models

from apps.users.api import serializers

# Create your models here.

class CourseModel(models.Model):
    title = models.CharField(max_length=255) #unique=True
    description = models.TextField(max_length=255)
    # department fk
    # instractor fk
    is_active = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class LessonModel(models.Model):

    CONTENT_TYPES = [
        ('video', 'Video'),
        ('pdf', 'PDF'),
        ('text', 'Text'),
        ('external', 'External Link'),
    ]

    course = models.ForeignKey(CourseModel, on_delete=models.CASCADE, related_name="lesson")
    title = models.CharField(max_length=255)
    content_type = models.CharField(max_length=20, choices=CONTENT_TYPES)
    content_url = models.URLField(blank=True, null=True)
    # file upload

    def __str__(self):
        return "Lesson " + str(self.title) + " of " + str(self.course) + " Course"


class QuizModel(models.Model):
    QUIZ_TYPES = [
        ("mcq", "MCQ"),
        ("short", "Short Answer"),
        ("mixed", "Mixes Questions")
    ]
    #########
    course = models.ForeignKey(CourseModel, on_delete=models.CASCADE, related_name="quizzes") # drop down menu
    lessons = models.ManyToManyField(LessonModel, related_name="quizzes")
    #########
    title = models.CharField(max_length=150)
    quiz_type = models.CharField(max_length=10, choices=QUIZ_TYPES)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} ({self.quiz_type}) on Course-{self.course}: Lessons-{self.lessons}"

class MCQQuestionModel(models.Model):
    #########
    quiz = models.ForeignKey(QuizModel, on_delete=models.CASCADE, related_name = "mcq_questions")
    #########
    text = models.CharField(max_length=150)

class MCQOptionModel(models.Model):
    #########
    question = models.ForeignKey(MCQQuestionModel, on_delete=models.CASCADE, related_name="options")
    #########
    text = models.CharField(max_length=255)
    is_correct = models.BooleanField(default=False)

class ShortAnswerQuestionModel(models.Model):
    #########
    quiz = models.ForeignKey(QuizModel, on_delete=models.CASCADE, related_name = "short_questions")
    #########
    text = models.CharField(max_length=150)
    # ans = models.CharField(max_length=255)
    # correct_ans = models.CharField(max_length=255)
