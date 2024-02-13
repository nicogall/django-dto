from django.db import models

import django_dto


class TestModelForeignKey(models.Model, django_dto.DTOMixin):
    char_field = models.CharField(max_length=128)


class TestModelForeignKeyNotSupportingDjangoDTO(models.Model):
    char_field = models.CharField(max_length=128)


class TestModel(models.Model, django_dto.DTOMixin):
    char_field = models.CharField(max_length=128)
    integer_field = models.IntegerField()
    date_time = models.DateTimeField(null=True)
    foreign_key = models.ForeignKey(
        TestModelForeignKey,
        on_delete=models.CASCADE,
        null=True,
        related_name="test_model",
    )
    m2m = models.ManyToManyField(TestModelForeignKey, related_name="test_model_m2m")


class TestModelNotSupportingDjangoDTO(models.Model, django_dto.DTOMixin):
    char_field = models.CharField(max_length=128)
    integer_field = models.IntegerField()
    date_time = models.DateTimeField(null=True)
    foreign_key = models.ForeignKey(
        TestModelForeignKeyNotSupportingDjangoDTO, on_delete=models.CASCADE, null=True
    )
