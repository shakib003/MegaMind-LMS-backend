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

    def get(self, request):
        courses = CourseModel.objects.all()  # Queryset: fetch all course records from the database
        serializer = CourseSerializer(courses, many=True)  # Convert queryset to Python native datatypes (list of dicts)
        return Response(serializer.data)  # Return serialized data as JSON (default: HTTP 200 OK)

    def post(self, request):
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



class CourseDescription(APIView): # get(), put(), patch(), delete()

    def get(self, request, pk):
        course = get_object_or_404(CourseModel, pk=pk)
        serializer = CourseSerializer(course)
        return Response(serializer.data)

    def put(self, request, pk):
        return self.update(request, pk)

    def patch(self, request, pk):
        return self.update(request, pk, partial=True)

    def update(self, request, pk, partial=False):
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
        course = get_object_or_404(CourseModel, pk=pk)
        course.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class LessonList(ListCreateAPIView): # get()
    serializer_class = LessonSerializer

    def get_queryset(self):
        pk = self.kwargs["pk"]
        return LessonModel.objects.filter(course=pk)

