from dataclasses import fields
from rest_framework import serializers

from apps.courses.models import (CourseModel, LessonModel, MCQOptionModel, MCQQuestionModel,
                                 QuizModel, ShortAnswerQuestionModel)


class LessonSerializer(serializers.ModelSerializer):

    course = serializers.ReadOnlyField(source='course.title')

    class Meta:
        model = LessonModel
        fields = "__all__"


class CourseSerializer(serializers.ModelSerializer):

    lesson = LessonSerializer(many=True, read_only=True) # Nested serializer

    class Meta:
        model = CourseModel
        fields = "__all__"

class MCQOptionSerializer(serializers.ModelSerializer):
    """
    Serializer for MCQ options.
    Serializes the option text and whether it is correct.
    """
    class Meta:
        model = MCQOptionModel
        fields = ["id", "text", "is_correct"]

class MCQQuestonSerializer(serializers.ModelSerializer):
    """
    Serializer for MCQ questions.
    Serializes the question text and its associated options.
    Supports bulk creation of options.
    """
    options = MCQOptionSerializer(many=True)

    class Meta:
        model = MCQQuestionModel
        fields = ["id", "text", "options"] # ["id", "Q_text", ["Op_text", "is_correct"]]

    def create(self, validated_data): # Creating questions with options
        """
        Create an MCQ question and its options.
        """
        options_data = validated_data.pop("options") # options_data = ["Op_text", "is_correct"]
        question = MCQQuestionModel.objects.create(**validated_data) # question = ["Q_text"]
        for options_data in options_data:
            MCQOptionModel.objects.create(question=question, **options_data)
        return question

class ShortAnswerQuestionSerializer(serializers.ModelSerializer):
    """
    Serializer for short answer questions.
    Serializes the question text.
    """
    class Meta:
        model = ShortAnswerQuestionModel
        fields = ["id", "text", "ans", "correct_ans"]

class QuizSerializer(serializers.ModelSerializer):
    """
    Serializer for quizzes.
    Serializes quiz details, associated lessons, and questions (MCQ and short answer).
    Supports bulk creation of questions and linking to lessons.
    """
    mcq_questions = MCQQuestonSerializer(many=True, required=False)
    short_questions = ShortAnswerQuestionSerializer(many=True, required=False)
    lessons = serializers.PrimaryKeyRelatedField(queryset=LessonModel.objects.all(), many=True)

    class Meta:
        model = QuizModel
        fields = ["id", "course", "lessons", "title", "quiz_type", 'mcq_questions', 'short_questions', 'created_at']

    def create(self, validated_data):
        """
        Create a quiz, link it to lessons, and bulk create questions.
        """
        lessons = validated_data.pop("lesson")
        mcq_questions = validated_data.pop("mcq_questions", [])
        short_questions = validated_data.pop("short_questions", [])
        quiz = QuizModel.objects.create(**validated_data)
        quiz.lessons.set(lessons)
        for que in mcq_questions:
            options = que.pop("options")
            question = MCQQuestionModel.objects.create(quiz=quiz, **que)
            for opt in options:
                MCQOptionModel.objects.create(question=question, **opt)
        for que in short_questions:
            ShortAnswerQuestionModel.objects.create(quiz=quiz, **que)
        return quiz



    """
    {
    "course": 1,
    "lessons": [2, 3],
    "title": "Sample Quiz",
    "quiz_type": "mcq",
    "mcq_questions": [
        {
        "text": "What is 2+2?", # que
        "options": [
            {"text": "3", "is_correct": false}, # que.pop()
            {"text": "4", "is_correct": true},
            {"text": "5", "is_correct": false}
        ]
        }
    ],
    "short_questions": [
        {
        "text": "Name a programming language that starts with P.",
        "ans": "",
        "correct_ans": "Python"
        }
    ]
    }

    """