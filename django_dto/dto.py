import dataclasses

from attr import dataclass
from django.db import models


class DjangoDTOException(Exception):
    _message = "Generic DjangoDTOException"

    def __init__(self, message=None):
        super().__init__(self, self._message or message)


class NotADjangoModel(DjangoDTOException):
    message = f"This is not a valid Django Model!"


class DataclassFieldNotFound(DjangoDTOException):
    message = "This dataclass does not have field"


class ValidationFailed(DjangoDTOException):
    message = "Type validation failed"


class DjangoDTONotEnabledOnForeignKey(DjangoDTOException):
    message = "Your Foreign Key does not support DjangoDTOException"


def build_dataclass_name_to_type_map(dataclass_cls) -> dict[str, type]:
    dataclass_fields = dataclasses.fields(dataclass_cls)
    return {
        dataclass_field.name: dataclass_field.type
        for dataclass_field in dataclass_fields
    }


types_map = {}


class DjangoDTOMixin:
    def to_dto(
        self, dataclass_cls, fields_map=None, validate_types=False, recurse=False
    ) -> dataclass:
        """
        fields_map: remaps the value of each model field to a dataclass field
        validate_types: is used to make sure that django model values are equal to dataclass types
        recurse: if True recursively access foreign keys
        """

        if not isinstance(self, models.Model):
            raise NotADjangoModel()

        # If a model field is defined here build a dataclass equivalent.
        fields_map = fields_map or {}

        dataclass_name_to_type = build_dataclass_name_to_type_map(dataclass_cls)

        dataclass_kwargs = {}

        for django_instance_field in self._meta.get_fields():
            django_instance_field_name = django_instance_field.name
            if django_instance_field_name in fields_map:
                dataclass_field_name = fields_map[django_instance_field_name]
                if dataclass_field_name not in dataclass_name_to_type:
                    raise DataclassFieldNotFound(
                        f"Field `{django_instance_field}` defined in `fields_map` found in Django instance, but the corresponding field `{fields_map[django_instance_field]}` is not defined in the dataclass"
                    )
                dataclass_field_name = fields_map[django_instance_field_name]
            else:
                dataclass_field_name = django_instance_field_name

            if dataclass_field_name in dataclass_name_to_type:
                django_value = getattr(self, django_instance_field_name)
                if validate_types and not isinstance(
                    django_value, dataclass_name_to_type[dataclass_field_name]
                ):
                    raise ValidationFailed(
                        f"{django_value} is not of type {dataclass_name_to_type[dataclass_field_name]}"
                    )
                if isinstance(django_value, models.Model):
                    if recurse and not isinstance(django_value, DjangoDTOMixin):
                        raise DjangoDTONotEnabledOnForeignKey()
                    if recurse:
                        dataclass_kwargs[dataclass_field_name] = django_value.to_dto(
                            dataclass_name_to_type[dataclass_field_name],
                            fields_map=fields_map.get(django_instance_field_name),
                            validate_types=validate_types,
                            recurse=recurse,
                        )
                    else:
                        dataclass_kwargs[dataclass_field_name] = None
                else:
                    dataclass_kwargs[dataclass_field_name] = django_value
        return dataclass_cls(**dataclass_kwargs)
