from urllib import request
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework import generics
from rest_framework.response import Response
from rest_framework import status
from rest_framework.generics import (ListAPIView, ListCreateAPIView,
                                     RetrieveUpdateAPIView, RetrieveUpdateDestroyAPIView)

from apps.courses.models import CourseModel, LessonModel
from apps.courses.api.serializers import CourseSerializer, LessonSerializer
from apps.users.api import serializers


class CourseList(APIView):
    """
    API View for listing all courses and creating a new course.
    """

    def get(self, request):
        """
        Retrieve all courses.

        Returns:
            - 200 OK: List of all courses.
        """
        courses = CourseModel.objects.all()
        serializer = CourseSerializer(courses, many=True)
        return Response(serializer.data)

    def post(self, request):
        """
        Create a new course.

        - Validates input data.
        - Checks for duplicate course title.
        - Saves and returns the new course if valid.

        Returns:
            - 201 Created: On success.
            - 400 Bad Request: On validation or duplicate error.
        """
        serializer = CourseSerializer(data=request.data)
        if serializer.is_valid():
            title = serializer.validated_data.get("title")
            if CourseModel.objects.filter(title=title).exists():
                return Response(
                    {"duplicate error": "A course with this title already exists."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CourseDescription(APIView):
    """
    API View for retrieving, updating, and deleting a specific course.
    """

    def get(self, request, pk):
        """
        Retrieve a course by its primary key.

        Returns:
            - 200 OK: Course data.
            - 404 Not Found: If course does not exist.
        """
        course = get_object_or_404(CourseModel, pk=pk)
        serializer = CourseSerializer(course)
        return Response(serializer.data)

    def put(self, request, pk):
        """
        Update a course completely.

        Returns:
            - 200 OK: Updated course data.
            - 400 Bad Request: On validation or duplicate error.
        """
        return self.update(request, pk)

    def patch(self, request, pk):
        """
        Partially update a course.

        Returns:
            - 200 OK: Updated course data.
            - 400 Bad Request: On validation or duplicate error.
        """
        return self.update(request, pk, partial=True)

    def update(self, request, pk, partial=False):
        """
        Helper method for updating a course.

        - Validates input data.
        - Checks for duplicate title (excluding current course).
        - Saves and returns updated course if valid.

        Returns:
            - 200 OK: Updated course data.
            - 400 Bad Request: On validation or duplicate error.
        """
        course = get_object_or_404(CourseModel, pk=pk)
        serializer = CourseSerializer(course, data=request.data, partial=partial)
        if serializer.is_valid():
            new_title = serializer.validated_data.get("title")
            if new_title and CourseModel.objects.filter(title=new_title).exclude(pk=pk).exists():
                return Response(
                    {"duplicate error": "A course with this title already exists."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        """
        Delete a course by its primary key.

        Returns:
            - 204 No Content: On successful deletion.
            - 404 Not Found: If course does not exist.
        """
        course = get_object_or_404(CourseModel, pk=pk)
        course.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class LessonList(APIView):
    """
    API View to list all lessons for a specific course (GET)
    and to create a new lesson under that course (POST).
    """

    def get(self, request, pk):
        """
        Retrieve all lessons for a specific course.

        Args:
            pk (int): The primary key (ID) of the course.

        Returns:
            - 200 OK: List of lessons for the course.
        """
        lessons = LessonModel.objects.filter(course=pk)
        serializer = LessonSerializer(lessons, many=True)
        return Response(serializer.data)

    def post(self, request, pk):
        """
        Create a new lesson under a specific course.

        - Validates input data.
        - Checks for duplicate lesson title within the course.
        - Saves and returns the new lesson if valid.

        Args:
            pk (int): The primary key (ID) of the course.

        Returns:
            - 201 Created: On success.
            - 400 Bad Request: On validation or duplicate error.
        """
        serializer = LessonSerializer(data=request.data)
        if serializer.is_valid():
            title = serializer.validated_data.get("title")
            if LessonModel.objects.filter(title=title, course=pk).exists():
                return Response(
                    {"duplicate error": "There is already a lesson with the same title under this course."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            serializer.save(course_id=pk)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LessonDescription(APIView):
    """
    API View for retrieving, updating, and deleting a specific lesson under a specific course.
    URL: /api/v1/course/{course_id}/lesson/{lesson_id}/
    """

    def filter_object_by(self, course_id, lesson_id):
        """
        Helper function to fetch the lesson object using both course_id and lesson_id.
        Ensures the lesson belongs to the given course.

        Returns:
            - LessonModel instance if found.
            - 404 Not Found: If lesson does not exist or does not belong to the course.
        """
        return get_object_or_404(LessonModel, course_id=course_id, id=lesson_id)

    def get(self, request, course_id, lesson_id):
        """
        Retrieve a specific lesson under a specific course.

        Returns:
            - 200 OK: Lesson data.
            - 404 Not Found: If lesson does not exist or does not belong to the course.
        """
        lesson = self.filter_object_by(course_id, lesson_id)
        serializer = LessonSerializer(lesson)
        return Response(serializer.data)

    def put(self, request, course_id, lesson_id):
        """
        Update a specific lesson under a specific course.

        Returns:
            - 200 OK: Updated lesson data.
            - 400 Bad Request: On validation error.
            - 404 Not Found: If lesson does not exist or does not belong to the course.
        """
        lesson = self.filter_object_by(course_id, lesson_id)
        serializer = LessonSerializer(lesson, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, course_id, lesson_id):
        """
        Delete a specific lesson under a specific course.

        Returns:
            - 204 No Content: On successful deletion.
            - 404 Not Found: If lesson does not exist or does not belong to the course.
        """
        lesson = self.filter_object_by(course_id, lesson_id)
        lesson.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
