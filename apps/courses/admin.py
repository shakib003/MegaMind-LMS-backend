from django.contrib import admin

from .models import (CourseModel, LessonModel, QuizModel,
                     MCQQuestionModel, MCQOptionModel, ShortAnswerQuestionModel)
# Register your models here.

admin.site.register(CourseModel)
admin.site.register(LessonModel)
admin.site.register(QuizModel)
admin.site.register(MCQQuestionModel)
admin.site.register(MCQOptionModel)
admin.site.register(ShortAnswerQuestionModel)