import os
import time
from django.conf import settings
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = 'Deletes shared state JSON files older than 24 hours.'

    def handle(self, *args, **kwargs):
        directory = os.path.join(settings.MEDIA_ROOT, "shared_states")
        max_age_seconds = 60 * 60 * 24  # 24 hours

        if not os.path.exists(directory):
            self.stdout.write("No shared_states directory found.")
            return

        deleted = 0
        now = time.time()
        for filename in os.listdir(directory):
            file_path = os.path.join(directory, filename)
            if filename.endswith(".json") and os.path.isfile(file_path):
                if now - os.path.getmtime(file_path) > max_age_seconds:
                    os.remove(file_path)
                    deleted += 1

        self.stdout.write(f"✅ Deleted {deleted} expired shared state files.")
