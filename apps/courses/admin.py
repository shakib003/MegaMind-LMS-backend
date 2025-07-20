from django.contrib import admin

from .models import CourseModel
from .models import LessonModel
# Register your models here.

admin.site.register(CourseModel)
admin.site.register(LessonModel)