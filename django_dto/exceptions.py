class DjangoDTOException(Exception):
    pass


class NotADjangoModel(DjangoDTOException):
    pass


class DjangoFieldNotFound(DjangoDTOException):
    pass


class ValidationFailed(DjangoDTOException):
    pass


class CantBuildDataclass(DjangoDTOException):
    pass


class NotADataclass(DjangoDTOException):
    pass


class FieldsMapKeyError(DjangoDTOException):
    pass
