from rest_framework.views import APIView
from rest_framework import generics
from rest_framework import mixins
from rest_framework.generics import ListAPIView, ListCreateAPIView, RetrieveUpdateAPIView


from apps.courses.models import CourseModel, LessonModel
from apps.courses.api.serializers import CourseSerializer, LessonSerializer


class CourseList(ListCreateAPIView): # get(), post()
    queryset =  CourseModel.objects.all()
    serializer_class = CourseSerializer

# class CourseCreate()

class CourseDescription(RetrieveUpdateAPIView): # get(), put(), patch()
    serializer_class = CourseSerializer

    def get_queryset(self):
        pk = self.kwargs["pk"]
        return CourseModel.objects.filter(pk=pk)


class LessonList(ListCreateAPIView): # get()
    serializer_class = LessonSerializer

    def get_queryset(self):
        pk = self.kwargs["pk"]
        return LessonModel.objects.filter(course=pk)

