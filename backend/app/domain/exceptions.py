class TaskNotFoundError(Exception):
    pass


class TaskAuthorizationError(Exception):
    pass


class AssigneeNotFoundError(Exception):
    pass


class InvalidStatusChangeError(Exception):
    pass
