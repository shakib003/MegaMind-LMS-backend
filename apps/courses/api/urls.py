from django.urls import path
from . views import (CourseList,
                     CourseDescription, LessonList)

urlpatterns = [
    path("all/", CourseList.as_view(), name="course-list"),
    path("<int:pk>/", CourseDescription.as_view(), name="course-description"),
    path("<int:pk>/lessons/", LessonList.as_view(), name="course_lesson-list")
]