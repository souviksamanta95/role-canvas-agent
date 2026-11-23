from django.db import models


class Sensitivity(models.IntegerChoices):
    """Ordered data sensitivity. Higher means more sensitive."""

    PUBLIC = 0, "Public"
    INTERNAL = 1, "Internal"
    CONFIDENTIAL = 2, "Confidential"
    RESTRICTED = 3, "Restricted"
