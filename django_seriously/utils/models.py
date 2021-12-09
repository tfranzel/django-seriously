import uuid

from django.db import models


class BaseModel(models.Model):
    """Opinionated Django base model"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        """
        Because the default is ridiculous. This guarantees that validation
        logic is executed in every non-bulk save situation. This comes at
        the expense of potentially running validation more than once.
        """
        self.full_clean()
        return super().save(*args, **kwargs)
