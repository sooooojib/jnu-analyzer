"""
Django management command to purge expired sessions and temporary files.
Run via cron or Render/Heroku/Fly.io scheduled jobs:
    python manage.py purge_expired_sessions
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.sessions_manager.models import ResultSession


class Command(BaseCommand):
    help = "Purges expired result sessions and deletes temporary uploaded files from disk."

    def add_arguments(self, parser):
        parser.add_argument(
            "--all",
            action="store_true",
            help="Purge ALL sessions, even if not yet expired (maintenance / reset mode).",
        )

    def handle(self, *args, **options):
        now = timezone.now()
        
        if options["all"]:
            sessions_to_purge = ResultSession.objects.all()
            self.stdout.write(self.style.WARNING("Running in PURGE ALL mode..."))
        else:
            sessions_to_purge = ResultSession.objects.filter(expires_at__lt=now)

        total_found = sessions_to_purge.count()
        if total_found == 0:
            self.stdout.write(self.style.SUCCESS("No expired sessions found. Ephemeral storage is clean."))
            return

        purged_files = 0
        for session in sessions_to_purge:
            if session.file_path:
                session.purge_file()
                purged_files += 1
            session.delete()

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully purged {total_found} session(s) and deleted {purged_files} file(s) from disk."
            )
        )
