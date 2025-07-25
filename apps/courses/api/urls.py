from django.urls import path
from . views import (CourseList, CourseDescription,
                    LessonList, LessonDescription, CourseQuizList, CourseQuizDescription)


# api/v1/course/... 
urlpatterns = [
    path("all/", CourseList.as_view(), name="course-list"),
    path("<int:pk>/", CourseDescription.as_view(), name="course-description"),
    path("<int:pk>/lesson/all/", LessonList.as_view(), name="course_lesson-list"),
    path("<int:course_id>/lesson/<int:lesson_id>/", LessonDescription.as_view(), name="course_lesson_description"),
    path("<int:course_id>/mini-quizze/all/", CourseQuizList.as_view(), name="course_quiz_list"),
    path("<int:course_id>/mini-quizze/a<int:quiz_id>/", CourseQuizDescription.as_view(), name="course_quiz_list")
]