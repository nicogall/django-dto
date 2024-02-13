import dataclasses
import datetime
from time import timezone

import pytest
from django.utils import timezone

from django_dto import dto, exceptions
from tests import models


@pytest.mark.django_db
def test_to_dto_should_convert_django_model_to_dataclass(faker):
    @dataclasses.dataclass
    class TestDataclass:
        char_field: str
        integer_field: str
        date_time: datetime.datetime

    date_time = timezone.now()
    char_field = faker.first_name()
    integer_field = faker.pyint()

    m = models.TestModel.objects.create(
        char_field=char_field, integer_field=integer_field, date_time=date_time
    )
    assert m.to_dto(TestDataclass) == TestDataclass(
        char_field=char_field, integer_field=integer_field, date_time=date_time
    )


@pytest.mark.django_db
def test_to_dto_should_ignore_additional_model_fields_wrt_dataclass(faker):
    @dataclasses.dataclass
    class TestDataclass:
        char_field: str
        integer_field: str

    date_time = timezone.now()
    char_field = faker.first_name()
    integer_field = faker.pyint()

    m = models.TestModel.objects.create(
        char_field=char_field, integer_field=integer_field, date_time=date_time
    )
    assert m.to_dto(TestDataclass) == TestDataclass(
        char_field=char_field, integer_field=integer_field
    )


@pytest.mark.django_db
def test_to_dto_fields_map(faker):
    @dataclasses.dataclass
    class TestDataclass:
        _char_field: str
        _integer_field: str
        _date_time: datetime.datetime

    date_time = timezone.now()
    char_field = faker.first_name()
    integer_field = faker.pyint()

    m = models.TestModel.objects.create(
        char_field=char_field, integer_field=integer_field, date_time=date_time
    )
    assert m.to_dto(
        TestDataclass,
        fields_map={
            "char_field": "_char_field",
            "integer_field": "_integer_field",
            "date_time": "_date_time",
        },
    ) == TestDataclass(
        _char_field=char_field, _integer_field=integer_field, _date_time=date_time
    )


@pytest.mark.django_db
def test_dto_validation_enabled(faker):
    @dataclasses.dataclass
    class TestDataclass:
        char_field: str
        integer_field: str
        # date_time is of type datetime in the Model, so translation is going to fail
        date_time: str

    date_time = timezone.now()
    char_field = faker.first_name()
    integer_field = faker.pyint()

    m = models.TestModel.objects.create(
        char_field=char_field, integer_field=integer_field, date_time=date_time
    )
    with pytest.raises(exceptions.ValidationFailed):
        m.to_dto(
            TestDataclass,
            validate_types=True,
        )


@pytest.mark.django_db
def test_to_dto_should_convert_django_model_with_foreign_key_to_dataclass(faker):
    @dataclasses.dataclass
    class ForeignKeyDataclass:
        char_field: str

    @dataclasses.dataclass
    class TestDataclass:
        char_field: str
        integer_field: str
        date_time: datetime.datetime
        foreign_key: ForeignKeyDataclass

    date_time = timezone.now()
    char_field = faker.first_name()
    integer_field = faker.pyint()
    foreign_key__char_field = faker.pystr()

    m = models.TestModel.objects.create(
        char_field=char_field,
        integer_field=integer_field,
        date_time=date_time,
        foreign_key=models.TestModelForeignKey.objects.create(
            char_field=foreign_key__char_field
        ),
    )
    # When recurse=False then foreign_key must be None
    assert m.to_dto(TestDataclass, recurse=False) == TestDataclass(
        char_field=char_field,
        integer_field=integer_field,
        date_time=date_time,
        foreign_key=None,
    )

    # When recurse=True then foreign key must be populated recursively
    assert m.to_dto(TestDataclass, recurse=True) == TestDataclass(
        char_field=char_field,
        integer_field=integer_field,
        date_time=date_time,
        foreign_key=ForeignKeyDataclass(char_field=foreign_key__char_field),
    )


@pytest.mark.django_db
def test_to_dto_should_succeed_if_recurse_and_validate_types_are_true_and_dtos_are_wellformed(
    faker,
):
    @dataclasses.dataclass
    class ForeignKeyDataclass:
        char_field: str

    @dataclasses.dataclass
    class TestDataclass:
        char_field: str
        integer_field: int
        date_time: datetime.datetime
        foreign_key: ForeignKeyDataclass

    date_time = timezone.now()
    char_field = faker.first_name()
    integer_field = faker.pyint()
    foreign_key__char_field = faker.pystr()

    m = models.TestModel.objects.create(
        char_field=char_field,
        integer_field=integer_field,
        date_time=date_time,
        foreign_key=models.TestModelForeignKey.objects.create(
            char_field=foreign_key__char_field
        ),
    )

    assert m.to_dto(TestDataclass, recurse=True, validate_types=True) == TestDataclass(
        char_field=char_field,
        integer_field=integer_field,
        date_time=date_time,
        foreign_key=ForeignKeyDataclass(char_field=foreign_key__char_field),
    )


@pytest.mark.django_db
def test_to_dto_should_fail_if_recurse_and_validate_types_are_true_and_fk_dtos_do_not_match_types(
    faker,
):
    @dataclasses.dataclass
    class ForeignKeyDataclass:
        char_field: int

    @dataclasses.dataclass
    class TestDataclass:
        char_field: str
        integer_field: int
        date_time: datetime.datetime
        foreign_key: ForeignKeyDataclass

    date_time = timezone.now()
    char_field = faker.first_name()
    integer_field = faker.pyint()
    foreign_key__char_field = faker.pystr()

    m = models.TestModel.objects.create(
        char_field=char_field,
        integer_field=integer_field,
        date_time=date_time,
        foreign_key=models.TestModelForeignKey.objects.create(
            char_field=foreign_key__char_field
        ),
    )

    with pytest.raises(exceptions.ValidationFailed):
        m.to_dto(TestDataclass, recurse=True, validate_types=True)


@pytest.mark.django_db
def test_to_dto_fields_map_and_respective_type_validation(faker):
    @dataclasses.dataclass
    class ForeignKeyDataclass:
        _char_field: int

    @dataclasses.dataclass
    class TestDataclass:
        _char_field: str
        _integer_field: int
        _date_time: datetime.datetime
        foreign_key: ForeignKeyDataclass

    date_time = timezone.now()
    char_field = faker.first_name()
    integer_field = faker.pyint()
    foreign_key__char_field = faker.pystr()

    m = models.TestModel.objects.create(
        char_field=char_field,
        integer_field=integer_field,
        date_time=date_time,
        foreign_key=models.TestModelForeignKey.objects.create(
            char_field=foreign_key__char_field
        ),
    )

    with pytest.raises(exceptions.ValidationFailed):
        m.to_dto(
            TestDataclass,
            recurse=True,
            validate_types=True,
            fields_map={
                "char_field": "_char_field",
                "integer_field": "_integer_field",
                "date_time": "_date_time",
                "foreign_key": {
                    "field_name": "foreign_key",
                    "submapping": {"char_field": "_char_field"},
                },
            },
        )


@pytest.mark.django_db
def test_to_dto_should_raise_cant_build_dataclass_if_mandatory_dataclass_fields_are_not_in_the_model(
    faker,
):
    @dataclasses.dataclass
    class TestDataclass:
        char_field: str
        integer_field: int
        missing_field: str

    date_time = timezone.now()
    char_field = faker.first_name()
    integer_field = faker.pyint()
    foreign_key__char_field = faker.pystr()

    m = models.TestModel.objects.create(
        char_field=char_field,
        integer_field=integer_field,
        date_time=date_time,
        foreign_key=models.TestModelForeignKey.objects.create(
            char_field=foreign_key__char_field
        ),
    )

    with pytest.raises(exceptions.CantBuildDataclass):
        m.to_dto(TestDataclass, validate_types=True, nullify_missing_fields=False)


@pytest.mark.django_db
def test_to_dto_succeeds_if_mandatory_data_class_fields_are_not_in_the_model_but_nullify_missing_dataclass_fields_true(
    faker,
):
    @dataclasses.dataclass
    class TestDataclass:
        char_field: str
        integer_field: int
        missing_field: str

    date_time = timezone.now()
    char_field = faker.first_name()
    integer_field = faker.pyint()
    foreign_key__char_field = faker.pystr()

    m = models.TestModel.objects.create(
        char_field=char_field,
        integer_field=integer_field,
        date_time=date_time,
        foreign_key=models.TestModelForeignKey.objects.create(
            char_field=foreign_key__char_field
        ),
    )

    m.to_dto(
        TestDataclass, validate_types=True, nullify_missing_fields=True
    ) == TestDataclass(
        char_field=char_field, integer_field=integer_field, missing_field=None
    )


@pytest.mark.django_db
def test_to_model_should_succeed_if_fields_can_be_mapped(
    faker,
):
    @dataclasses.dataclass
    class TestDataclass(dto.DjangoModelMixin):
        char_field: str
        integer_field: int
        date_time: datetime.datetime

    date_time = timezone.now()
    char_field = faker.first_name()
    integer_field = faker.pyint()

    test_dataclass = TestDataclass(
        char_field=char_field,
        integer_field=integer_field,
        date_time=date_time,
    )

    translated_django_model = test_dataclass.to_model(models.TestModel)
    # It can be saved!
    translated_django_model.save()
    translated_django_model.refresh_from_db()

    assert translated_django_model.char_field == test_dataclass.char_field
    assert translated_django_model.integer_field == test_dataclass.integer_field
    assert translated_django_model.date_time == test_dataclass.date_time


@pytest.mark.django_db
def test_to_model_should_succeed_if_fields_can_be_mapped_recursively(
    faker,
):
    @dataclasses.dataclass
    class ForeignKeyDataclass(dto.DjangoModelMixin):
        char_field: str

    @dataclasses.dataclass
    class TestDataclass(dto.DjangoModelMixin):
        char_field: str
        integer_field: int
        date_time: datetime.datetime
        foreign_key: ForeignKeyDataclass

    date_time = timezone.now()
    char_field = faker.first_name()
    integer_field = faker.pyint()
    foreign_key__char_field = faker.pystr()

    test_dataclass = TestDataclass(
        char_field=char_field,
        integer_field=integer_field,
        date_time=date_time,
        foreign_key=ForeignKeyDataclass(char_field=foreign_key__char_field),
    )

    translated_django_model = test_dataclass.to_model(models.TestModel, recurse=True)

    assert translated_django_model.char_field == test_dataclass.char_field
    assert translated_django_model.integer_field == test_dataclass.integer_field
    assert translated_django_model.date_time == test_dataclass.date_time
    assert (
        translated_django_model.foreign_key.char_field
        == test_dataclass.foreign_key.char_field
    )


@pytest.mark.django_db
def test_to_model_should_succeed_when_fields_can_be_mapped_with_field_renaming(
    faker,
):
    @dataclasses.dataclass
    class TestDataclass(dto.DjangoModelMixin):
        _char_field: str
        _integer_field: int
        _date_time: datetime.datetime

    _date_time = timezone.now()
    _char_field = faker.first_name()
    _integer_field = faker.pyint()

    test_dataclass = TestDataclass(
        _char_field=_char_field,
        _integer_field=_integer_field,
        _date_time=_date_time,
    )

    translated_django_model = test_dataclass.to_model(
        models.TestModel,
        fields_map={
            "_char_field": "char_field",
            "_integer_field": "integer_field",
            "_date_time": "date_time",
        },
    )

    assert translated_django_model.char_field == test_dataclass._char_field
    assert translated_django_model.integer_field == test_dataclass._integer_field
    assert translated_django_model.date_time == test_dataclass._date_time


@pytest.mark.django_db
def test_to_model_should_succeed_when_fields_can_be_mapped_with_field_renaming_and_recursively(
    faker,
):
    @dataclasses.dataclass
    class ForeignKeyDataclass(dto.DjangoModelMixin):
        _char_field: str

    @dataclasses.dataclass
    class TestDataclass(dto.DjangoModelMixin):
        _char_field: str
        _integer_field: int
        _date_time: datetime.datetime
        _foreign_key: ForeignKeyDataclass

    _date_time = timezone.now()
    _char_field = faker.first_name()
    _integer_field = faker.pyint()

    test_dataclass = TestDataclass(
        _char_field=_char_field,
        _integer_field=_integer_field,
        _date_time=_date_time,
        _foreign_key=ForeignKeyDataclass(_char_field=faker.pystr()),
    )

    translated_django_model = test_dataclass.to_model(
        models.TestModel,
        fields_map={
            "_char_field": "char_field",
            "_integer_field": "integer_field",
            "_date_time": "date_time",
            "_foreign_key": {
                "field_name": "foreign_key",
                "submapping": {"_char_field": "char_field"},
            },
        },
        recurse=True,
    )

    assert translated_django_model.char_field == test_dataclass._char_field
    assert translated_django_model.integer_field == test_dataclass._integer_field
    assert translated_django_model.date_time == test_dataclass._date_time
    assert (
        translated_django_model.foreign_key.char_field
        == test_dataclass._foreign_key._char_field
    )
