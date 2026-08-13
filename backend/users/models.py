from django.contrib.auth.models import AbstractUser

from processes.models import AuthorisationProcess


class User(AbstractUser):
    """Custom user model extending Django's AbstractUser."""

    def is_reviewer(self) -> bool:
        """Check if user is a member of any reviewer group for any process.
        
        Returns True if the user's groups intersect with any process's reviewer_groups.
        Returns False for unauthenticated users.
        """
        if not self.is_authenticated:
            return False

        return AuthorisationProcess.reviewer_groups.through.objects.filter(
            group_id__in=self.groups.values("id")
        ).exists()
