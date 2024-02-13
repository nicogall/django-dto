import dataclasses

from django.db import models

from django_dto import exceptions


class DjangoField:
    def __init__(self, field: models.Field):
        self._field = field

    def is_foreign_key(self) -> bool:
        return bool(self._field.related_model)

    def is_m2m(self) -> bool:
        return isinstance(self._field, models.ManyToManyField)

    @property
    def name(self) -> str:
        return self._field.name

    @property
    def type(self) -> type:
        # We don't provide a type for django fields, but we need it for foreign keys
        if self.is_foreign_key():
            return self._field.related_model
        return None


class DjangoModelAnalyzer:
    def __init__(self, django_model_cls):
        if not issubclass(django_model_cls, models.Model):
            raise exceptions.NotADjangoModel(
                f"`{self.__class__.__name__}` is not a valid Django Model!"
            )

        self._django_model_cls: type[models.Model] = django_model_cls
        self._fields: list[DjangoField] = {
            DjangoField(field).name: DjangoField(field)
            for field in self._django_model_cls._meta.get_fields()
            if not DjangoField(field).is_m2m()
        }

    def get_fields(self) -> list[DjangoField]:
        return self._fields.values()

    def get_field(self, field_name: str) -> DjangoField:
        if field_name not in self._fields:
            raise AttributeError(
                f"Field `{field_name}` not found in Django model {self._django_model_cls.__name__}"
            )
        return self._fields[field_name]

    def get_field_type(self, field_name: str) -> type:
        return self.get_field(field_name).type

    def get_field_names(self) -> list[str]:
        return self._fields.keys()

    def is_field_available(self, field_name: str) -> bool:
        return field_name in self._fields


class DataclassField:
    def __init__(self, field: dataclasses.Field):
        self._field = field

    @property
    def name(self) -> str:
        return self._field.name

    @property
    def type(self) -> type:
        return self._field.type

    def is_dataclass(self) -> bool:
        return dataclasses.is_dataclass(self.type)


class DataclassAnalyser:
    def __init__(self, dataclass_cls: type):
        if not dataclasses.is_dataclass(dataclass_cls):
            raise exceptions.NotADataclass(
                f"`{dataclass_cls.__name__}` is not a valid dataclass!"
            )

        self._dataclass_cls = dataclass_cls
        self._dataclass_fields = {
            field.name: DataclassField(field)
            for field in dataclasses.fields(dataclass_cls)
        }

    def get_field_names(self) -> list[str]:
        return self._dataclass_fields.keys()

    def is_field_available(self, field_name: str) -> bool:
        return field_name in self._dataclass_fields()

    def get_field_type(self, field_name: str) -> any:
        return self._dataclass_fields[field_name].type

    def get_field(self, field_name: str) -> DataclassField:
        return self._dataclass_fields[field_name]


class DjangoModelInstance:
    def __init__(self, django_model_instance: models.Model):
        self._django_model_instance = django_model_instance
        self._django_model_analyser = DjangoModelAnalyzer(type(django_model_instance))

    def get_value(self, field_name: str) -> any:
        if not self._django_model_analyser.is_field_available(field_name):
            raise exceptions.DjangoFieldNotFound(
                f"Field `{field_name}` not found in Django instance"
            )
        return getattr(self._django_model_instance, field_name)

    def get_class_name(self) -> str:
        return self._django_model_instance.__class__.__name__


class DataclassInstance:
    def __init__(self, dataclass_instance: any):
        self._dataclass_instance = dataclass_instance

    def get_value(self, field_name: str) -> any:
        return getattr(self._dataclass_instance, field_name)


class DjangoInstanceToDataclassTranslator:
    def __init__(
        self, django_model_instance: models.Model, dataclass_cls: any, fields_map: dict
    ):
        self._django_model_instance = DjangoModelInstance(django_model_instance)
        self._dataclass_cls = dataclass_cls
        self._django_model_analyser = DjangoModelAnalyzer(type(django_model_instance))
        self._dataclass_analyser = DataclassAnalyser(dataclass_cls)
        self._fields_map = fields_map or {}

    def _get_corresponding_dataclass_field_name(self, django_field_name: str) -> str:
        if django_field_name in self._fields_map:
            if isinstance(self._fields_map[django_field_name], dict):
                field_name = self._fields_map[django_field_name].get("field_name")
                if not field_name:
                    raise exceptions.FieldsMapKeyError(
                        f"Can't find `field_name` key in the `fields_map` value for `{django_field_name}`"
                    )
            else:
                field_name = self._fields_map.get(django_field_name)
                if not field_name:
                    raise exceptions.FieldsMapKeyError(
                        f"Can't find `{django_field_name}` key in the `fields_map`."
                    )
        else:
            field_name = django_field_name

        return field_name

    def _get_corresponding_dataclass_field_submapping(
        self, django_field_name: str
    ) -> dict:
        if django_field_name in self._fields_map and isinstance(
            self._fields_map[django_field_name], dict
        ):
            return self._fields_map[django_field_name].get("submapping", {})
        return {}

    def _get_mappable_django_field_names(self) -> list[DjangoField]:
        """
        Returns a list of Django fields that can be mapped to the dataclass.
        """
        dataclass_field_names = self._dataclass_analyser.get_field_names()
        return [
            self._django_model_analyser.get_field(django_field_name)
            for django_field_name in self._django_model_analyser.get_field_names()
            if self._get_corresponding_dataclass_field_name(django_field_name)
            in dataclass_field_names
        ]

    def translate(
        self, validate_types: bool, recurse: bool, nullify_missing_fields: bool
    ):
        dataclass_kwargs = {}
        for field in self._get_mappable_django_field_names():
            dataclass_field_name = self._get_corresponding_dataclass_field_name(
                field.name
            )
            if field.is_foreign_key():
                if recurse:
                    dataclass_field_value = DjangoInstanceToDataclassTranslator(
                        self._django_model_instance.get_value(field.name),
                        self._dataclass_analyser.get_field_type(dataclass_field_name),
                        self._get_corresponding_dataclass_field_submapping(field.name),
                    ).translate(validate_types, recurse, nullify_missing_fields)
                else:
                    dataclass_field_value = None
            else:
                dataclass_field_type = self._dataclass_analyser.get_field_type(
                    dataclass_field_name
                )
                dataclass_field_value = self._django_model_instance.get_value(
                    field.name
                )
                if (
                    validate_types
                    and type(dataclass_field_value) != dataclass_field_type
                ):
                    raise exceptions.ValidationFailed(
                        f"`{dataclass_field_value}` from `{self._django_model_instance.get_class_name()}.{dataclass_field_name}` does not match type `{dataclass_field_type}`"
                    )

            dataclass_kwargs[dataclass_field_name] = dataclass_field_value

        if nullify_missing_fields:
            for field_name in self._dataclass_analyser.get_field_names():
                if field_name not in dataclass_kwargs:
                    dataclass_kwargs[field_name] = None

        try:
            return self._dataclass_cls(**dataclass_kwargs)
        except TypeError as e:
            raise exceptions.CantBuildDataclass(
                f"Some mandatory arguments are missing and dataclass can't be built. "
                "See full stacktrace for more details or set `nullify_missing_fields` "
                "to True to fill missing fields with None."
            ) from e


class DataclassToDjangoInstanceTranslator:
    def __init__(
        self,
        dataclass_instance: models.Model,
        django_model_cls: type[models.Model],
        fields_map: dict,
    ):
        self._dataclass_instance = DataclassInstance(dataclass_instance)
        self._django_model_cls = django_model_cls
        self._dataclass_analyser = DataclassAnalyser(type(dataclass_instance))
        self._django_model_analyser = DjangoModelAnalyzer(django_model_cls)
        self._fields_map = fields_map or {}

    def _get_corresponding_django_field_name(self, dataclass_field_name: str) -> str:
        if dataclass_field_name in self._fields_map:
            if isinstance(self._fields_map[dataclass_field_name], dict):
                field_name = self._fields_map[dataclass_field_name].get("field_name")
                if not field_name:
                    raise exceptions.FieldsMapValueError(
                        f"Can't find `field_name` key in the `fields_map` value for `{dataclass_field_name}`"
                    )
            else:
                field_name = self._fields_map[dataclass_field_name]
        else:
            field_name = dataclass_field_name

        return field_name

    def _get_corresponding_django_field_submapping(
        self, dataclass_field_name: str
    ) -> dict:
        if dataclass_field_name in self._fields_map and isinstance(
            self._fields_map[dataclass_field_name], dict
        ):
            return self._fields_map[dataclass_field_name].get("submapping", {})
        return {}

    def _get_mappable_dataclass_fields(self) -> list[DataclassField]:
        """
        Returns a list of dataclass fields that can be mapped to the Django model.
        """
        django_field_names = self._django_model_analyser.get_field_names()
        return [
            self._dataclass_analyser.get_field(dataclass_field_name)
            for dataclass_field_name in self._dataclass_analyser.get_field_names()
            if self._get_corresponding_django_field_name(dataclass_field_name)
            in django_field_names
        ]

    def translate(self, recurse: bool, nullify_missing_fields: bool):
        django_model_kwargs = {}
        for field in self._get_mappable_dataclass_fields():
            django_field_name = self._get_corresponding_django_field_name(field.name)
            if field.is_dataclass():
                if recurse:
                    django_field_value = DataclassToDjangoInstanceTranslator(
                        self._dataclass_instance.get_value(field.name),
                        self._django_model_analyser.get_field_type(django_field_name),
                        self._get_corresponding_django_field_submapping(field.name),
                    ).translate(recurse, nullify_missing_fields)
                else:
                    django_field_value = None
            else:
                django_field_value = self._dataclass_instance.get_value(field.name)
            django_model_kwargs[django_field_name] = django_field_value

        if nullify_missing_fields:
            for field_name in self._django_model_analyser.get_field_names():
                if field_name not in django_model_kwargs:
                    django_model_kwargs[field_name] = None

        try:
            return self._django_model_cls(**django_model_kwargs)
        except TypeError as e:
            raise exceptions.CantBuildDataclass(
                f"Some mandatory arguments are missing and dataclass can't be built. "
                "See full stacktrace for more details or set `nullify_missing_fields` "
                "to True to fill missing fields with None."
            ) from e
