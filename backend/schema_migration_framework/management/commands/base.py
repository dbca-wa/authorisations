"""Base class for schema migration management commands."""

from django.core.management.base import BaseCommand


class SchemaMigrationBaseCommand(BaseCommand):
    """Base command for schema migration operations.
    
    Subclasses must define `target_key` attribute.
    """

    target_key: str = None  # Subclasses must override

    def get_target_key(self) -> str:
        """Get the target key for this command.
        
        Returns:
            Target key string (e.g., "questionnaires").
        
        Raises:
            NotImplementedError: If subclass doesn't define target_key.
        """
        if self.target_key is None:
            raise NotImplementedError(
                f"{self.__class__.__name__} must define target_key attribute"
            )
        return self.target_key
