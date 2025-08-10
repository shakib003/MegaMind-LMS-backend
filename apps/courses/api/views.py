from urllib import request
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework import generics
from rest_framework.response import Response
from rest_framework import status
from rest_framework.generics import (ListAPIView, ListCreateAPIView,
                                     RetrieveUpdateAPIView, RetrieveUpdateDestroyAPIView,
                                     )
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework import serializers

from apps.courses.models import CourseModel, LessonModel, QuizModel
from apps.courses.api.serializers import (CourseSerializer, LessonSerializer,
                                          QuizSerializer, LessonPDFQnASerializer)
from apps.users.api import serializers
from rest_framework import serializers

import os
from dotenv import load_dotenv
import requests
import json

# Import the new search function from vector_utils
from ..vector_utils import search_index

from rest_framework.permissions import IsAuthenticated
from apps.users.api.permissions import IsTeacherUser, IsStudentUser, IsEnrolledStudent
from apps.users.models import User

class CourseList(APIView):
    """
    API View for listing all courses and creating a new course.

    URLs:
        - GET  /api/v1/course/all/      : List all courses
        - POST /api/v1/course/all/      : Create a new course
    """

    permission_classes = [IsAuthenticated, IsTeacherUser]

    @extend_schema(
        summary="List all courses",
        responses=CourseSerializer(many=True),
    )

    def get(self, request):
        """
        Retrieve all courses.

        Returns:
            - 200 OK: List of all courses.
        """
        courses = CourseModel.objects.all()
        serializer = CourseSerializer(courses, many=True)
        return Response(serializer.data)

    @extend_schema(
        summary="Create a new course",
        request=CourseSerializer,
        responses=CourseSerializer,
        examples=[
            OpenApiExample(
                "Course Example",
                value={"title": "Math 101", "description": "Basic math course"}
            )
        ]
    )

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
    permission_classes = [IsAuthenticated, IsTeacherUser]

    @extend_schema(
        summary="Retrieve a course",
        responses=CourseSerializer,
        parameters=[OpenApiParameter("pk", int, OpenApiParameter.PATH)],
    )
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

    @extend_schema(
        summary="Update a course completely",
        request=CourseSerializer,
        responses=CourseSerializer,
        parameters=[OpenApiParameter("pk", int, OpenApiParameter.PATH)],
    )
    def put(self, request, pk):
        """
        Update a course completely.

        Returns:
            - 200 OK: Updated course data.
            - 400 Bad Request: On validation or duplicate error.
        """
        return self.update(request, pk)

    @extend_schema(
        summary="Partially update a course",
        request=CourseSerializer,
        responses=CourseSerializer,
        parameters=[OpenApiParameter("pk", int, OpenApiParameter.PATH)],
    )
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

    @extend_schema(
        summary="Delete a course",
        responses={204: None},
        parameters=[OpenApiParameter("pk", int, OpenApiParameter.PATH)],
    )
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

    permission_classes = [IsAuthenticated, IsTeacherUser]

    @extend_schema(
        summary="List all lessons for a course",
        responses=LessonSerializer(many=True),
        parameters=[OpenApiParameter("pk", int, OpenApiParameter.PATH)],
    )
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


    @extend_schema(
        summary="Create a new lesson under a course",
        request=LessonSerializer,
        responses=LessonSerializer,
        parameters=[OpenApiParameter("pk", int, OpenApiParameter.PATH)],
        examples=[
            OpenApiExample(
                "Lesson Example",
                value={
                    "title": "Introduction",
                    "content_type": "video",
                    "content_url": "https://example.com/video.mp4"
                }
            )
        ]
    )
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

    permission_classes = [IsAuthenticated, IsTeacherUser]

    def filter_object_by(self, course_id, lesson_id):
        """
        Helper function to fetch the lesson object using both course_id and lesson_id.
        Ensures the lesson belongs to the given course.

        Returns:
            - LessonModel instance if found.
            - 404 Not Found: If lesson does not exist or does not belong to the course.
        """
        return get_object_or_404(LessonModel, course_id=course_id, id=lesson_id)

    @extend_schema(
        summary="Retrieve a lesson",
        responses=LessonSerializer,
        parameters=[
            OpenApiParameter("course_id", int, OpenApiParameter.PATH),
            OpenApiParameter("lesson_id", int, OpenApiParameter.PATH),
        ],
    )
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

    @extend_schema(
        summary="Update a lesson",
        request=LessonSerializer,
        responses=LessonSerializer,
        parameters=[
            OpenApiParameter("course_id", int, OpenApiParameter.PATH),
            OpenApiParameter("lesson_id", int, OpenApiParameter.PATH),
        ],
    )
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

    @extend_schema(
        summary="Delete a lesson",
        responses={204: None},
        parameters=[
            OpenApiParameter("course_id", int, OpenApiParameter.PATH),
            OpenApiParameter("lesson_id", int, OpenApiParameter.PATH),
        ],
    )
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

    permission_classes = [IsAuthenticated, IsTeacherUser]

    @extend_schema(
        summary="List all quizzes for a course",
        responses=QuizSerializer(many=True),
        parameters=[OpenApiParameter("course_id", int, OpenApiParameter.PATH)],
    )
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

    @extend_schema(
        summary="Create a new quiz under a course",
        request=QuizSerializer,
        responses=QuizSerializer,
        parameters=[OpenApiParameter("course_id", int, OpenApiParameter.PATH)],
        examples=[
            OpenApiExample(
                "Quiz Example",
                value={
                    "course": 1,
                    "lessons": [2, 3],
                    "title": "Sample Quiz",
                    "quiz_type": "mcq",
                    "mcq_questions": [
                        {
                            "text": "What is 2+2?",
                            "options": [
                                {"text": "3", "is_correct": False},
                                {"text": "4", "is_correct": True},
                                {"text": "5", "is_correct": False}
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
            )
        ]
    )
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

    permission_classes = [IsAuthenticated, IsTeacherUser]

    @extend_schema(
        summary="Retrieve a quiz",
        responses=QuizSerializer,
        parameters=[
            OpenApiParameter("course_id", int, OpenApiParameter.PATH),
            OpenApiParameter("quiz_id", int, OpenApiParameter.PATH),
        ],
    )
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

    @extend_schema(
        summary="Delete a quiz",
        responses={204: None},
        parameters=[
            OpenApiParameter("course_id", int, OpenApiParameter.PATH),
            OpenApiParameter("quiz_id", int, OpenApiParameter.PATH),
        ],
    )
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




class LessonMiniQuizList(APIView):
    """
    API View to list, create, and delete all quizzes for a specific lesson in a specific course.
    """

    permission_classes = [IsAuthenticated, IsTeacherUser]

    @extend_schema(
        summary="List all quizzes for a lesson in a course",
        responses=QuizSerializer(many=True),
        parameters=[
            OpenApiParameter("course_id", int, OpenApiParameter.PATH, description="ID of the course"),
            OpenApiParameter("lesson_id", int, OpenApiParameter.PATH, description="ID of the lesson"),
        ],
    )
    def get(self, request, course_id, lesson_id):
        """
        List all quizzes linked to a specific lesson in a specific course.
        """
        lesson = get_object_or_404(LessonModel, pk=lesson_id, course_id=course_id)
        quizzes = QuizModel.objects.filter(course_id=course_id, lessons=lesson)
        serializer = QuizSerializer(quizzes, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Create a new quiz for a lesson in a course",
        request=QuizSerializer,
        responses=QuizSerializer,
        parameters=[
            OpenApiParameter("course_id", int, OpenApiParameter.PATH, description="ID of the course"),
            OpenApiParameter("lesson_id", int, OpenApiParameter.PATH, description="ID of the lesson"),
        ],
        examples=[
            OpenApiExample(
                "Quiz Example",
                value={
                    "course": 1,
                    "lessons": [2],  # lesson_id should be included here
                    "title": "Lesson Mini Quiz",
                    "quiz_type": "mcq",
                    "mcq_questions": [
                        {
                            "text": "What is 2+2?",
                            "options": [
                                {"text": "3", "is_correct": False},
                                {"text": "4", "is_correct": True},
                                {"text": "5", "is_correct": False}
                            ]
                        }
                    ],
                    "short_questions": [
                        {
                            "text": "Name a programming language that starts with P.",
                            "correct_ans": "Python"
                        }
                    ]
                }
            )
        ]
    )
    def post(self, request, course_id, lesson_id):
        """
        Create a new quiz for a specific lesson in a specific course.
        The lesson_id will be added to the lessons list if not present.
        """
        # Ensure the lesson exists and belongs to the course
        lesson = get_object_or_404(LessonModel, pk=lesson_id, course_id=course_id)

        data = request.data.copy()
        data['course'] = course_id
        # Ensure the lesson is included in the lessons list
        lessons = data.get('lessons', [])
        if str(lesson_id) not in [str(l) for l in lessons]:
            lessons.append(lesson_id)
        data['lessons'] = lessons
        serializer = QuizSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        summary="Delete all quizzes for a lesson in a course",
        responses={204: None},
        parameters=[
            OpenApiParameter("course_id", int, OpenApiParameter.PATH, description="ID of the course"),
            OpenApiParameter("lesson_id", int, OpenApiParameter.PATH, description="ID of the lesson"),
        ],
    )
    def delete(self, request, course_id, lesson_id):
        """
        Delete all quizzes linked to a specific lesson in a specific course.
        """
        lesson = get_object_or_404(LessonModel, pk=lesson_id, course_id=course_id)
        quizzes = QuizModel.objects.filter(course_id=course_id, lessons=lesson)
        deleted_count = quizzes.count()
        quizzes.delete()
        return Response(
            {"detail": f"Deleted {deleted_count} quizzes for lesson {lesson_id} in course {course_id}."},
            status=status.HTTP_204_NO_CONTENT
        )


class LessonMiniQuizDescription(APIView):
    """
    API View for retrieving, updating, and deleting a specific quiz for a lesson in a course.
    """

    permission_classes = [IsAuthenticated, IsTeacherUser]

    @extend_schema(
        summary="Retrieve a specific quiz for a lesson in a course",
        responses=QuizSerializer,
        parameters=[
            OpenApiParameter("course_id", int, OpenApiParameter.PATH, description="ID of the course"),
            OpenApiParameter("lesson_id", int, OpenApiParameter.PATH, description="ID of the lesson"),
            OpenApiParameter("quiz_id", int, OpenApiParameter.PATH, description="ID of the quiz"),
        ],
    )
    def get(self, request, course_id, lesson_id, quiz_id):
        """
        Retrieve a specific quiz for a lesson in a course.
        """
        lesson = get_object_or_404(LessonModel, pk=lesson_id, course_id=course_id)
        quiz = get_object_or_404(QuizModel, pk=quiz_id, course_id=course_id, lessons=lesson)
        serializer = QuizSerializer(quiz)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Update a specific quiz for a lesson in a course",
        request=QuizSerializer,
        responses=QuizSerializer,
        parameters=[
            OpenApiParameter("course_id", int, OpenApiParameter.PATH, description="ID of the course"),
            OpenApiParameter("lesson_id", int, OpenApiParameter.PATH, description="ID of the lesson"),
            OpenApiParameter("quiz_id", int, OpenApiParameter.PATH, description="ID of the quiz"),
        ],
    )
    def put(self, request, course_id, lesson_id, quiz_id):
        """
        Update a specific quiz for a lesson in a course.
        """
        lesson = get_object_or_404(LessonModel, pk=lesson_id, course_id=course_id)
        quiz = get_object_or_404(QuizModel, pk=quiz_id, course_id=course_id, lessons=lesson)
        data = request.data.copy()
        data['course'] = course_id
        lessons = data.get('lessons', [])
        if str(lesson_id) not in [str(l) for l in lessons]:
            lessons.append(lesson_id)
        data['lessons'] = lessons
        serializer = QuizSerializer(quiz, data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        summary="Delete a specific quiz for a lesson in a course",
        responses={204: None},
        parameters=[
            OpenApiParameter("course_id", int, OpenApiParameter.PATH, description="ID of the course"),
            OpenApiParameter("lesson_id", int, OpenApiParameter.PATH, description="ID of the lesson"),
            OpenApiParameter("quiz_id", int, OpenApiParameter.PATH, description="ID of the quiz"),
        ],
    )
    def delete(self, request, course_id, lesson_id, quiz_id):
        """
        Delete a specific quiz for a lesson in a course.
        """
        lesson = get_object_or_404(LessonModel, pk=lesson_id, course_id=course_id)
        quiz = get_object_or_404(QuizModel, pk=quiz_id, course_id=course_id, lessons=lesson)
        quiz.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


def query_generative_model(prompt):
    """
    Sends a prompt to the local generative model using Ollama and returns the response.
    """
    url = "http://localhost:11434/api/generate"
    payload = {
        "model": "tinyllama",
        "prompt": prompt,
        "stream": False
    }
    response = requests.post(url, json=payload)
    response.raise_for_status()
    response_text = response.text
    last_response = json.loads(response_text.strip().split('\n')[-1])
    return last_response.get("response", "")


class LessonPDFQnA(APIView):

    permission_classes = [IsAuthenticated, IsTeacherUser, IsStudentUser]

    parser_classes = [JSONParser]

    @extend_schema(
        summary="Ask a question about the lesson's PDF content using Vector Search",
        request=LessonPDFQnASerializer,
        responses={"200": serializers.CharField()},
        parameters=[
            OpenApiParameter("course_id", int, OpenApiParameter.PATH),
            OpenApiParameter("lesson_id", int, OpenApiParameter.PATH),
        ],
    )
    def post(self, request, course_id, lesson_id):
        """
        Answers a question based on the content of the lesson's PDF using
        FAISS vector search and a local TinyLlama model.
        """
        lesson = get_object_or_404(LessonModel, pk=lesson_id, course_id=course_id)
        if not lesson.pdf_file:
            return Response({"error": "No PDF uploaded for this lesson."}, status=400)

        question = request.data.get("question")
        if not question:
            return Response({"error": "No question provided."}, status=400)

        # --- REPLACED LOGIC ---
        # Instead of reading the PDF here, we search the pre-built index.
        try:
            context = search_index(lesson_id, question)
        except Exception as e:
            return Response({"error": f"Failed to search the vector index: {e}"}, status=500)
        # --- END OF REPLACED LOGIC ---

        # Compose the prompt with the highly relevant context
        prompt = f"Using only the following context, please answer the question.\n\nContext:\n{context}\n\nQuestion: {question}\n\nAnswer:"

        # Call the local language model to generate the final answer
        try:
            answer = query_generative_model(prompt)
        except Exception as e:
            return Response({"error": f"Failed to get a response from the AI model: {e}"}, status=500)

        return Response({"answer": answer})


class AddStudentToCourseView(APIView):
    permission_classes = [IsAuthenticated, IsTeacherUser]

    def post(self, request, teacher_id, course_id):
        try:
            student_id = request.data.get('student_id')
            course = CourseModel.objects.get(id=course_id)
            student = User.objects.get(student_id=student_id, role='student')
            course.students.add(student)
            return Response({"message": "Student added to course successfully."}, status=status.HTTP_200_OK)
        except CourseModel.DoesNotExist:
            return Response({"error": "Course not found."}, status=status.HTTP_404_NOT_FOUND)
        except User.DoesNotExist:
            return Response({"error": "Student not found."}, status=status.HTTP_404_NOT_FOUND)


class StudentCourseListView(generics.ListAPIView):
    serializer_class = CourseSerializer
    permission_classes = [IsAuthenticated, IsStudentUser]

    def get_queryset(self):
        return self.request.user.enrolled_courses.all()


class StudentCourseDetailView(generics.RetrieveAPIView):
    serializer_class = CourseSerializer
    permission_classes = [IsAuthenticated, IsStudentUser, IsEnrolledStudent]
    queryset = CourseModel.objects.all()


class StudentLessonListView(generics.ListAPIView):
    serializer_class = LessonSerializer
    permission_classes = [IsAuthenticated, IsStudentUser]

    def get_queryset(self):
        course_id = self.kwargs.get('course_id')
        return LessonModel.objects.filter(course_id=course_id)


class StudentLessonDetailView(generics.RetrieveAPIView):
    serializer_class = LessonSerializer
    permission_classes = [IsAuthenticated, IsStudentUser]
    queryset = LessonModel.objects.all()