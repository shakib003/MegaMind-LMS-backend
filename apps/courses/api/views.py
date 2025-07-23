from urllib import request
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework import generics
from rest_framework.response import Response
from rest_framework import status
from rest_framework.generics import (ListAPIView, ListCreateAPIView,
                                     RetrieveUpdateAPIView, RetrieveUpdateDestroyAPIView)

from apps.courses.models import CourseModel, LessonModel, QuizModel
from apps.courses.api.serializers import CourseSerializer, LessonSerializer, QuizSerializer
from apps.users.api import serializers


class CourseList(APIView):
    """
    API View for listing all courses and creating a new course.

    URLs:
        - GET  /api/v1/course/all/      : List all courses
        - POST /api/v1/course/all/      : Create a new course
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

    URLs:
        - GET    /api/v1/course/<int:pk>/      : Retrieve a course
        - PUT    /api/v1/course/<int:pk>/      : Update a course completely
        - PATCH  /api/v1/course/<int:pk>/      : Partially update a course
        - DELETE /api/v1/course/<int:pk>/      : Delete a course
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

    URLs:
        - GET  /api/v1/course/<int:pk>/lesson/all/      : List all lessons for a course
        - POST /api/v1/course/<int:pk>/lesson/all/      : Create a new lesson under a course
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

    URLs:
        - GET    /api/v1/course/<int:course_id>/lesson/<int:lesson_id>/      : Retrieve a lesson
        - PUT    /api/v1/course/<int:course_id>/lesson/<int:lesson_id>/      : Update a lesson
        - DELETE /api/v1/course/<int:course_id>/lesson/<int:lesson_id>/      : Delete a lesson
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


class CourseQuizList(APIView):
    """
    API View to list all quizzes for a specific course (GET)
    and to create a new quiz under that course (POST).

    URLs:
        - GET  /api/v1/course/<int:course_id>/mini-quizze/all/      : List all quizzes for a course
        - POST /api/v1/course/<int:course_id>/mini-quizze/all/      : Create a new quiz under a course
    """

    def get(self, request, course_id):
        """
        Retrieve all quizzes for a specific course.

        Args:
            course_id (int): The primary key (ID) of the course.

        Returns:
            - 200 OK: List of quizzes for the course.
        """
        quizzes = QuizModel.objects.filter(course_id=course_id)
        serializer = QuizSerializer(quizzes, many=True)
        return Response(serializer.data)

    def post(self, request, course_id):
        """
        Create a new quiz under a specific course.

        - Validates input data.
        - Supports bulk creation of MCQ and short-answer questions.
        - Links the quiz to one or more lessons.

        Args:
            course_id (int): The primary key (ID) of the course.

        Returns:
            - 201 Created: On success.
            - 400 Bad Request: On validation error.
        """
        data = request.data.copy()
        data['course'] = course_id
        serializer = QuizSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class CourseQuizDescription(APIView):
    """
    API View for retrieving and deleting a specific quiz under a specific course.

    URLs:
        - GET    /api/v1/course/<int:course_id>/mini-quizze/a<int:quiz_id>/      : Retrieve a quiz
        - DELETE /api/v1/course/<int:course_id>/mini-quizze/a<int:quiz_id>/      : Delete a quiz
    """

    def get(self, request, course_id, quiz_id):
        """
        Retrieve a specific quiz under a specific course.

        Args:
            course_id (int): The primary key (ID) of the course.
            quiz_id (int): The primary key (ID) of the quiz.

        Returns:
            - 200 OK: Quiz data.
            - 404 Not Found: If quiz does not exist or does not belong to the course.
        """
        quiz = get_object_or_404(QuizModel, course_id=course_id, id=quiz_id)
        serializer = QuizSerializer(quiz)
        return Response(serializer.data)

    def delete(self, request, course_id, quiz_id):
        """
        Delete a specific quiz under a specific course.

        Args:
            course_id (int): The primary key (ID) of the course.
            quiz_id (int): The primary key (ID) of the quiz.

        Returns:
            - 204 No Content: On successful deletion.
            - 404 Not Found: If quiz does not exist or does not belong to the course.
        """
        quiz = get_object_or_404(QuizModel, course_id=course_id, id=quiz_id)
        quiz.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)