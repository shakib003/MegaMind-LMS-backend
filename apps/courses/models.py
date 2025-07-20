from django.db import models

# Create your models here.

class CourseModel(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(max_length=255)
    # department fk
    # instractor fk
    is_active = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class LessonModel(models.Model):

    CONTENT_TYPES = [
        ('video', 'Video'),
        ('pdf', 'PDF'),
        ('text', 'Text'),
        ('external', 'External Link'),
    ]

    course = models.ForeignKey(CourseModel, on_delete=models.CASCADE, related_name="lesson")
    title = models.CharField(max_length=255)
    content_type = models.CharField(max_length=20, choices=CONTENT_TYPES)
    content_url = models.URLField(blank=True, null=True)
    # file upload

    def __str__(self):
        return "Lesson " + str(self.title) + " of " + str(self.course) + " Course"


