from django.contrib import admin

from .models import (CourseModel, LessonModel, QuizModel)
# Register your models here.

admin.site.register(CourseModel)
admin.site.register(LessonModel)
admin.site.register(QuizModel)