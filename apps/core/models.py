from django.contrib.auth import get_user_model
from django.db import models
from django.db.models import JSONField

User = get_user_model()


class MultiLanguageModel(models.Model):
    """Abstract model for multilingual content."""
    name = models.CharField(max_length=255, null=True, blank=True)
    name_ru = models.CharField(max_length=255, null=True, blank=True)
    name_kr = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        abstract = True


class TimestampedModel(models.Model):
    """Abstract model for timestamp tracking."""
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Stamp(MultiLanguageModel):
    icon = models.ImageField(upload_to='stamp_icons', blank=True, null=True)
    """Vehicle brand/manufacturer model."""

    def __str__(self):
        return self.name

    class Meta:
        db_table = "car_stamp"
        indexes = [
            models.Index(fields=["name"]),
            models.Index(fields=["name_ru"]),
            models.Index(fields=["name_kr"]),

        ]


class Model(MultiLanguageModel):
    """Vehicle model."""
    stamp = models.ForeignKey(
        Stamp,
        on_delete=models.CASCADE,
        related_name="car_model"
    )

    def __str__(self):
        return self.name

    class Meta:
        db_table = "car_model"
        indexes = [
            models.Index(fields=["name"]),
            models.Index(fields=["name_ru"]),
            models.Index(fields=["name_kr"]),
            models.Index(fields=["stamp"]),
        ]


class Generation(MultiLanguageModel):
    """Vehicle generation."""
    model = models.ForeignKey(
        Model,
        on_delete=models.CASCADE,
        related_name="car_generation"
    )

    def __str__(self):
        return self.name

    class Meta:
        db_table = "car_generation"
        indexes = [
            models.Index(fields=["name"]),
            models.Index(fields=["name_ru"]),
            models.Index(fields=["model"]),
        ]


class Fuel(MultiLanguageModel):
    """Fuel type model."""

    def __str__(self):
        return self.name

    class Meta:
        db_table = "fuel"
        indexes = [
            models.Index(fields=["name"]),
            models.Index(fields=["name_ru"]),
        ]


class Transmission(MultiLanguageModel):
    """Transmission type model."""

    def __str__(self):
        return self.name

    class Meta:
        db_table = "transmission"
        indexes = [
            models.Index(fields=["name"]),
            models.Index(fields=["name_ru"]),
        ]


class Color(MultiLanguageModel):
    """Vehicle color model."""
    code = models.CharField(max_length=20, unique=True)
    icon = models.CharField(max_length=20, blank=True, null=True)

    def __str__(self):
        return f"{self.code} ({self.name_ru})"

    class Meta:
        db_table = "color"
        indexes = [
            models.Index(fields=["code"]),
            models.Index(fields=["name"]),
            models.Index(fields=["name_ru"]),
            models.Index(fields=["name_kr"]),
        ]


class CarGeneralInfo(TimestampedModel):
    """Optimized car model with better performance for filtering."""
    stamp = models.ForeignKey(Stamp, on_delete=models.CASCADE, related_name="cars")
    model = models.ForeignKey(Model, on_delete=models.CASCADE, related_name="cars")
    generation = models.ForeignKey(Generation, on_delete=models.CASCADE, related_name="cars", blank=True, null=True)
    year = models.PositiveSmallIntegerField()
    engine_volume = models.DecimalField(max_digits=5, decimal_places=2,null=True, blank=True)
    salon_color = models.ForeignKey(Color, on_delete=models.CASCADE, related_name="cars", null=True, blank=True)
    SALON_TYPE_CHOICES = [
        ('LEATHER', 'Кожа'),
        ('FABRIC', 'Ткань'),
        ('ALCANTARA', 'Алькантара'),
        ('VINYL', 'Винил'),
        ('WOOD', 'Дерево'),
        ('CARBON', 'Карбон'),
        ('PLASTIC', 'Пластик'),
    ]
    salon_type = models.CharField(
        max_length=20,
        choices=SALON_TYPE_CHOICES, null=True, blank=True
    )

    BODY_TYPE_CHOICES = [
        ('SEDAN', 'Седан'),
        ('HATCHBACK', 'Хэтчбек'),
        ('SUV', 'Внедорожник'),
        ('COUPE', 'Купе'),
        ('CONVERTIBLE', 'Кабриолет'),
        ('PICKUP', 'Пикап'),
        ('WAGON', 'Универсал'),
        ('VAN', 'Фургон'),
    ]
    body_type = models.CharField(
        max_length=20,
        choices=BODY_TYPE_CHOICES, default='SUV', null=True, blank=True
    )

    horse_power = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        help_text="Engine power in horsepower"
    )
    drive = models.CharField(
        max_length=20,
        choices=[
            ('fwd', 'Передний привод'),
            ('rwd', 'Задний привод'),
            ('awd', 'Полный привод'),
            ('4wd', 'Привод 4x4'),
        ],
        null=True,
        blank=True,
        help_text="Drive type of the vehicle"
    )

    primary_color = models.ForeignKey(
        Color,
        on_delete=models.CASCADE,
        related_name="primary_cars", blank=True, null=True
    )
    primary_fuel_type = models.ForeignKey(
        Fuel,
        on_delete=models.CASCADE,
        related_name="primary_cars"
    )
    primary_transmission = models.ForeignKey(
        Transmission,
        on_delete=models.CASCADE,
        related_name="primary_cars"
    )

    seats_count = models.PositiveSmallIntegerField(default=4)
    external_id = models.CharField(max_length=255, blank=True, null=True)
    vin = models.CharField(max_length=255, blank=True, null=True)
    features = JSONField(default=dict, blank=True, null=True)

    def __str__(self):
        return f"{self.stamp} {self.model} ({self.year})"

    class Meta:
        ordering = ["-created_at"]
        db_table = "car_general_info"
        indexes = [
            models.Index(fields=["year"]),
            models.Index(fields=["horse_power"]),
            models.Index(fields=["drive"]),
            models.Index(fields=["stamp", "model"]),
            models.Index(fields=["primary_fuel_type", "primary_transmission"]),
            models.Index(fields=["horse_power", "drive"]),
            models.Index(fields=["year", "horse_power"]),
            models.Index(fields=["-created_at"]),
            models.Index(fields=["stamp"]),
            models.Index(fields=["model"]),
            models.Index(fields=["generation"]),
            models.Index(fields=["primary_color"]),
        ]
