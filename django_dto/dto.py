from django.db import models

from django_dto import core


class DTOMixin:
    def to_dto(
        self,
        dataclass_cls: type,
        fields_map: dict = None,
        validate_types: bool = False,
        recurse: bool = False,
        nullify_missing_fields: bool = False,
    ) -> type:
        """
        Converts a Django model instance to a dataclass instance.

        Args:
            dataclass_cls: The dataclass class to convert the model instance to.
            fields_map (Optional): A dictionary that remaps the value of each model field to a dataclass field.
            validate_types (Optional): If True, validates that the Django model values are of the same type as the dataclass types.
            recurse (Optional): If True, recursively accesses foreign keys.
            nullify_missing_fields (Optional): If True, fills missing fields in the dataclass with None.

        Returns:
            dataclass: The converted dataclass instance.

        Note:
            - If a model field is defined in the `fields_map`, it will be used to build a dataclass equivalent.
            - If `recurse` is True, foreign keys will be recursively accessed and converted to dataclass instances.
            - If `nullify_missing_fields` is True, mandatory fields in the dataclass that are not present in the model will be filled with None.
        """

        return core.DjangoInstanceToDataclassTranslator(
            self, dataclass_cls, fields_map
        ).translate(validate_types, recurse, nullify_missing_fields)


class DTOModel(models.Model, DTOMixin):
    class Meta:
        abstract = True


class DjangoModelMixin:
    def to_model(
        self,
        django_model_cls: type[models.Model],
        fields_map: dict = None,
        recurse: bool = False,
        nullify_missing_fields: bool = False,
    ) -> models.Model:
        """
        Converts a dataclass instance to a Django model instance.

        Args:
            django_model_cls: The Django model class to convert to.
            fields_map: A dictionary that maps dataclass field names to model field names. Defaults to None.
            recurse: If True, recursively access foreign keys. Defaults to False.

        Returns:
            django.db.models.Model: The converted Django model instance.
        """
        return core.DataclassToDjangoInstanceTranslator(
            self, django_model_cls, fields_map
        ).translate(recurse, nullify_missing_fields)
