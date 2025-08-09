from django.apps import AppConfig

# The class name 'UsersConfig' appears to be a typo in the original file.
# It should likely be 'CoursesConfig'. I am using the original name to match the file.
class UsersConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.courses"
    label = "courses"

    def ready(self):
        # This method is called when the Django app is initialized.
        # It's the proper place to import and connect signals.
        import apps.courses.signals
