from django.urls import path
from .views import (
    CourseList, CourseDescription, LessonList, LessonDescription,
    CourseQuizList, CourseQuizDescription, LessonMiniQuizList,
    LessonMiniQuizDescription, LessonPDFQnA, AddStudentToCourseView,
    StudentCourseListView, StudentCourseDetailView, StudentLessonListView,
    StudentLessonDetailView
)

# api/v1/course/...
urlpatterns = [
    path("all/", CourseList.as_view(), name="course-list"),
    path("<int:pk>/", CourseDescription.as_view(), name="course-description"),
    path("<int:pk>/lesson/all/", LessonList.as_view(), name="course_lesson-list"),
    path("<int:course_id>/lesson/<int:lesson_id>/", LessonDescription.as_view(), name="course_lesson_description"),

    path("<int:course_id>/quizze/all/", CourseQuizList.as_view(), name="course_quiz_list"),
    path("<int:course_id>/quizze/<int:quiz_id>/", CourseQuizDescription.as_view(), name="course_quiz_list"),

    path("<int:course_id>/lesson/<int:lesson_id>/mini-quiz/all/", LessonMiniQuizList.as_view(), name="course_quiz_list"),
    path("<int:course_id>/lesson/<int:lesson_id>/mini-quiz/<int:quiz_id>/", LessonMiniQuizDescription.as_view(), name="course_quiz_list"),

    path(
        "<int:course_id>/lesson/<int:lesson_id>/pdf-qna/",
        LessonPDFQnA.as_view(),
        name="lesson_pdf_qna"
    ),

    path('<int:teacher_id>/add-student-to-course/<int:course_id>/', AddStudentToCourseView.as_view(), name='add-student-to-course'),
    path('student/courses/', StudentCourseListView.as_view(), name='student-courses'),
    path('student/course/<int:pk>/', StudentCourseDetailView.as_view(), name='student-course-detail'),
    path('student/course/<int:course_id>/lessons/', StudentLessonListView.as_view(), name='student-lessons'),
    path('student/course/<int:course_id>/lesson/<int:pk>/', StudentLessonDetailView.as_view(), name='student-lesson-detail'),
]