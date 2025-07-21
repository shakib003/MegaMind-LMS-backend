from dataclasses import fields
from rest_framework import serializers

from apps.courses.models import CourseModel, LessonModel


class LessonSerializer(serializers.ModelSerializer):

    course = serializers.ReadOnlyField(source='course.title')

    class Meta:
        model = LessonModel
        fields = "__all__"


class CourseSerializer(serializers.ModelSerializer):

    lesson = LessonSerializer(many=True, read_only=True)

    class Meta:
        model = CourseModel
        fields = "__all__"

