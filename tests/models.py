from django.db import models

from django_dto import DjangoDTOMixin


class TestModelForeignKey(models.Model, DjangoDTOMixin):
    char_field = models.CharField(max_length=128)


class TestModelForeignKeyNotSupportingDjangoDTO(models.Model):
    char_field = models.CharField(max_length=128)


class TestModel(models.Model, DjangoDTOMixin):
    char_field = models.CharField(max_length=128)
    integer_field = models.IntegerField()
    date_time = models.DateTimeField(null=True)
    foreign_key = models.ForeignKey(
        TestModelForeignKey, on_delete=models.CASCADE, null=True
    )


class TestModelNotSupportingDjangoDTO(models.Model, DjangoDTOMixin):
    char_field = models.CharField(max_length=128)
    integer_field = models.IntegerField()
    date_time = models.DateTimeField(null=True)
    foreign_key = models.ForeignKey(
        TestModelForeignKeyNotSupportingDjangoDTO, on_delete=models.CASCADE, null=True
    )
