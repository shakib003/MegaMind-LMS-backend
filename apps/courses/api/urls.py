from django.urls import path
from . views import (CourseList,
                     CourseDescription, LessonList)


# api/v1/course/...
urlpatterns = [
    path("all/", CourseList.as_view(), name="course-list"),
    path("<int:pk>/", CourseDescription.as_view(), name="course-description"),
    path("<int:pk>/lesson/all", LessonList.as_view(), name="course_lesson-list")
]