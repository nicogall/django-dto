# django-dto

[![pypi](https://badge.fury.io/py/django-dto.svg)](https://pypi.org/project/django-dto/)
![test workflow](https://github.com/nicogall/django-dto/actions/workflows/test.yml/badge.svg)
[![codecov](https://codecov.io/gh/nicogall/django-dto/graph/badge.svg?token=DC8V5FPCKF)](https://codecov.io/gh/nicogall/django-dto)
![pyversions](https://img.shields.io/pypi/pyversions/django-dto.svg)
![djangoversions](https://img.shields.io/pypi/frameworkversions/django/django-dto)


**Django DTO** is a library 📚 that translates your django model instances to DTOs 🚀 and vice versa.

## Why?

In the context of clean (hexagonal) architecture, we are usually interested in separating database related objects (DAOs) from actual business objects.
Objects that are used to carry data across multiple components in software application are called [DTOs](https://en.wikipedia.org/wiki/Data_transfer_object).

Django is one of the most loved framework because of its powerful ORM, which gives developers unlimited power and simplicity when it comes to RDBMS access.
However, django components and libraries usually couple ORM models and `Queryset` objects to views and controllers, which is great to build applications fast, but painful when the size of the application grows significantly.

There are several reasons why passing or coupling ORM objects to other components of the application makes development harder. Some reasons include:

1. An ORM object has access to the underlying RDBMS. Which means that the view (or other components) can directly access the database. This makes debugging very complicated on large applications.

2. As a corollary of 1., we can't control how many queries we're making if ORM objects go everywhere without control.

3. An ORM object is tightly coupled to the underlying DB technology. If we want to use a different DBMS for a specific use case, we must likely rethink and touch all places where ORM objects are passed and used.

4. Column names enforced in the ORM Model are used everywhere and most likely not easy to change.

In order to avoid all the aforementioned situations, where the developer is forced to pass an ORM object around the app, it is useful to automatically build objects that are independent from the data source in the form of dataclasses.

This library give you the power to seamlessly convert a django model instance to a custom dataclass and vice versa.

This way most of the pain points highlighted above are solved because:

* DTOs are independent from the ORM and can be built without effort. 💪
* ORM objects can be kepts in a controlled environment (i.e. DAO). ✅
* Once the dataclass is defined, the underlying ORM is not relevant, we can switch easily to other data sources or DBMSes. ✅
* Column aren't an issue anymore as the library supports fields mapping between django models and dataclasses 🔠

## Features

### Supported
* Translation of a Django model instance to a python dataclass (DTO) ✅
* Translation of a python dataclass to a Django model ✅
* Mapping of field names between Django models and dataclasses ✅
* Type validation available in the process of Django ➡️ dataclass  conversion ✅
* Foreign keys support ✅

### Not supported
* Many to Many fields are ignored
* Type validation is not available while converting from dataclass to Django instance


## How it works?

### Basic usage
To illustrate how it works and the available interface, let's start with a real world example:

1. Create a django model and extend it with `DTOMixin`:
    ```python
    from django_dto import DTOMixin

    class User(models.Model, DTOMixin):
        name = models.CharField(max_length=255)
        surname = models.CharField(max_length=255)
        date_of_birth = models.DateField()
    ```

2. Create a target dataclass:
    ```python
    import dataclasses
    import datetime

    @dataclasses.dataclass
    class UserDTO:
        name: str
        surname: str
        date_of_birth: datetime.date
    ```

3. Create an instance of the model and save it:
    ```python
    In [1]: user = User.objects.create(name="John", surname="Smith", date_of_birth=datetime.datetime.now().date())

    Out [1]: <User: User object (1)>
    ```

4. Given `User` extends `DTOMixin` we can use `to_dto` method to convert our instance to `UserDTO` dataclass.
    ```python
    In [1]: user.to_dto(UserDTO)

    Out [1]: UserDTO(name='John', surname='Smith', date_of_birth=datetime.date(2024, 2, 12))
    ```

### Type validation
 It is possible to enforce type validation. When a model instance is converted to a dataclass, we can raise an error if the django value doesn't match the type expected by our dataclass. Let's see an example:
 ```python
@dataclasses.dataclass
class UserDTO:
    name: int
    surname: str
    date_of_birth: datetime.date
 ```

```python
In  [1]: user.to_dto(UserDTO, validate_types=True)
Out [1]: ValidationFailed: `John` from `User.name` does not match type `<class 'int'>`
```

### Foreign keys
As we know Django ORM behaves in a lazy way, data is only accessed if needed. For instance, a foreign key model instance is only retrieved from the RDBMS if the fk attribute is accessed (or `select_related` is used).
For instance:
```python
class User(models.Model, DTOMixin):
    name = models.CharField(max_length=255)
    surname = models.CharField(max_length=255)
    date_of_birth = models.DateField()


class UserFile(models.Model, DTOMixin):
    name = models.CharField(max_length=255)
    file_location = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)


class UserFileDTO:
    name: str
    file: str
    created_at: datetime.datetime
    updated_at: datetime.datetime
    user: UserDTO
```

Let's try to create a dto on a model with a foreign key:

```python
In  [1]: user_file = UserFile.objects.create(name="file_1.txt", file_location="uploads/file_1.txt", created_at=datetime.datetime.now(), updated_at=datetime.datetime.now(), user=user)

In  [2]: user_file.to_dto(UserFileDTO)
Out [2]: UserFileDTO(name='file_1.txt', file_location='uploads/file_1.txt', created_at=datetime.datetime(2024, 2, 12, 23, 12, 31, 854635, tzinfo=datetime.timezone.utc), updated_at=datetime.datetime(2024, 2, 12, 23, 12, 31, 854682, tzinfo=datetime.timezone.utc), user=None)
```

As you can see `user=None` because we're lazy as Django and we don't want to make unnecessary db queries. However you can set `recurse=True` to recursively access all foreign keys and map all dataclasses.
```python
In [1]: user_file.to_dto(UserFileDTO, recurse=True)

Out[1]: UserFileDTO(name='file_1.txt', file_location='uploads/file_1.txt', created_at=datetime.datetime(2024, 2, 12, 23, 12, 31, 854635, tzinfo=datetime.timezone.utc), updated_at=datetime.datetime(2024, 2, 12, 23, 12, 31, 854682, tzinfo=datetime.timezone.utc), user=UserDTO(name='John', surname='Smith'))
```

### Fields remapping
Another core feature is fields remapping. You may need to rename your fields easily when you build your dataclasses. For instance, your django model has a field called `name`, but the same field is called `my_special_name` in your dataclass.
You can just set a mapping dictionary when you call `to_dto` as shown below:
```python
class User(models.Model, DTOMixin):
    name = models.CharField(max_length=255)
    surname = models.CharField(max_length=255)
    date_of_birth = models.DateField()


@dataclasses.dataclass
class SpecialUserDTO:
    my_special_name: str
    surname: str
    date_of_birth: datetime.date

In [1]: user.to_dto(SpecialUserDTO, fields_map={"name": "my_special_name"})

Out[1]: SpecialUserDTO(my_special_name='John', surname='Smith', date_of_birth=datetime.date(2024, 2, 12))
```

And it also works recursively on foreign keys:

```python
@dataclass
class SpecialUserFileDTO:
    name: str
    file_location: str
    created_at: datetime.datetime
    updated_at: datetime.datetime
    special_user: SpecialUserDTO


In [1]: user_file.to_dto(SpecialUserFileDTO, fields_map={"user": {"field_name": "special_user", "submapping": {"name": "my_special_name"}}}, recurse=True)

Out[1]: SpecialUserFileDTO(name='file_1.txt', file_location='uploads/file_1.txt', created_at=datetime.datetime(2024, 2, 12, 23, 12, 31, 854635, tzinfo=datetime.timezone.utc), updated_at=datetime.datetime(2024, 2, 12, 23, 12, 31, 854682, tzinfo=datetime.timezone.utc), special_user=SpecialUserDTO(my_special_name='John', surname='Smith', date_of_birth=datetime.date(2024, 2, 12)))
```

### Missing fields nullification

During conversion, it may happen that our target dataclass requires some arguments that our django model doesn't provide. This is usually something you should fix, but it may be useful to provide a `None` default by passing `nullify_missing_fields=True`

```python
@dataclass
class UserFileDTO:
    name: str
    uploaded_by: UserDTO


In  [1]: user_file.to_dto(UserFileDTO)
Out [1]: CantBuildDataclass: Some mandatory arguments are missing and dataclass can't be built. See full stacktrace for more details or set `nullify_missing_fields` to True to fill missing fields with None.
```

The reason is `uploaded_by` is not defined in the `UserFile` model, but it's required to build the dataclass. In order to set `uploaded_by=None` automatically, execute the following:
```python
In [1]: user_file.to_dto(UserFileDTO, nullify_missing_fields=True)
Out[1]: UserFileDTO(name='file_1.txt', uploaded_by=None)
```

### From dataclass to Django model


#### Standard example
This library also supports the reverse operation. If you need to build a Django model instance from a dataclass, here's an example:
```python
@dataclass
class UserDTO(DjangoModelMixin):
    name: str
    surname: str
    date_of_birth: datetime.date

class User(models.Model, DTOMixin):
    name = models.CharField(max_length=255)
    surname = models.CharField(max_length=255)
    date_of_birth = models.DateField()

In [1]: UserDTO(name="John", surname="Smith", date_of_birth=datetime.datetime.now().date()).to_model(User)
Out[1]: <User: User object (None)>
```
**Please note that the django model instance `User` is not saved. You have to explicitly do `.save()` to write to your RDBMS.**


`to_model(django_model_cls: type[models.Model], fields_map: dict = None, recurse: bool = False, nullify_missing_fields: bool = False)` supports more or less the same arguments as `to_dto(...)`.

A more complex example is the following:
```python
@dataclass
class UserFileDTO(DjangoModelMixin):
    name: str
    file_location: str
    created_at: datetime.datetime
    updated_at: datetime.datetime
    user: UserDTO


@dataclass
class UserDTO(DjangoModelMixin):
    name: str
    surname: str
    date_of_birth: datetime.date

In [1]: user = UserDTO(name="John", surname="Smith", date_of_birth=datetime.datetime.now().date())

In [2]: user_file = UserFileDTO(name="file_1.txt", file_location="uploads/file_1.txt", created_at=datetime.datetime.now(), updated_at=datetime.datetime.now(), user=user)
```

As usual, to allow for the creation of a `User` django instance, we need to add `recurse=True`.

```python
In [1]: user_file_django_instance = user_file.to_model(UserFile, recurse=True)
```

in order to save our model instance we need to save both `user_file_django_instance.user` (foreign key) and `user_file_django_instance`:
```python
user_file_django_instance.user.save()
user_file_django_instance.save()
```


## Contributing

Feel free to open a PR if you spot bugs or possible improvements on the current implementation.
It is required to write a test if a new feature is added and this package must work with:
- Python (versions: 3.9, 3.10, 3.11, 3.12)
- Django (versions: 3, 4, 5)

In order to test these scenarios a `tox.ini` file is set up. Make sure to install all relevant python versions using `pyenv` and then run:
```
tox
```
