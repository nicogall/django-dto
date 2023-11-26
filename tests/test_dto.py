import dataclasses
import datetime
from time import timezone

import pytest
from django.utils import timezone

from django_dto import dto
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
def test_dto_fields_map(faker):
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
    with pytest.raises(dto.ValidationFailed):
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
def test_to_dto_should_fail_if_recurse_true_but_foreign_key_does_not_implement_django_dto_mixin(
    faker,
):
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

    m = models.TestModelNotSupportingDjangoDTO.objects.create(
        char_field=char_field,
        integer_field=integer_field,
        date_time=date_time,
        foreign_key=models.TestModelForeignKeyNotSupportingDjangoDTO.objects.create(
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
    with pytest.raises(dto.DjangoDTONotEnabledOnForeignKey):
        m.to_dto(TestDataclass, recurse=True) == TestDataclass(
            char_field=char_field,
            integer_field=integer_field,
            date_time=date_time,
            foreign_key=ForeignKeyDataclass(char_field=foreign_key__char_field),
        )
