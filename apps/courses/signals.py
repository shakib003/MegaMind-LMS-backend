from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import LessonModel
from .vector_utils import create_and_save_index
import threading

@receiver(post_save, sender=LessonModel)
def lesson_post_save(sender, instance, created, **kwargs):
    """
    Signal to trigger PDF indexing in a background thread after a LessonModel
    instance is saved.
    """
    # Check if the instance has a PDF file associated with it
    if instance.pdf_file:
        print(f"Signal received for lesson {instance.id}. Starting indexing thread.")
        # Run indexing in a non-blocking background thread
        thread = threading.Thread(target=create_and_save_index, args=(instance.id,))
        thread.start()