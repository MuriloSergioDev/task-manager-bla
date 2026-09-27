from uuid import uuid4

from app.domain.services.authorization_service import TaskAuthorizationService
from tests.fixtures.factories import build_task, build_user


def test_owner_can_view_edit_delete_assign_and_complete() -> None:
    owner = build_user()
    task = build_task(owner_id=owner.id, assigned_to=None)

    assert TaskAuthorizationService.can_view(owner, task) is True
    assert TaskAuthorizationService.can_edit(owner, task) is True
    assert TaskAuthorizationService.can_delete(owner, task) is True
    assert TaskAuthorizationService.can_assign(owner, task) is True
    assert TaskAuthorizationService.can_complete(owner, task) is True


def test_assignee_can_view_edit_and_complete_but_not_delete_or_reassign() -> None:
    owner = build_user()
    assignee = build_user()
    task = build_task(owner_id=owner.id, assigned_to=assignee.id)

    assert TaskAuthorizationService.can_view(assignee, task) is True
    assert TaskAuthorizationService.can_complete(assignee, task) is True
    assert TaskAuthorizationService.can_edit(assignee, task) is True
    assert TaskAuthorizationService.can_delete(assignee, task) is False
    assert TaskAuthorizationService.can_assign(assignee, task) is False


def test_unrelated_user_cannot_view_or_do_anything_else() -> None:
    owner = build_user()
    stranger = build_user()
    task = build_task(owner_id=owner.id, assigned_to=None)

    assert TaskAuthorizationService.can_view(stranger, task) is False
    assert TaskAuthorizationService.can_edit(stranger, task) is False
    assert TaskAuthorizationService.can_delete(stranger, task) is False
    assert TaskAuthorizationService.can_assign(stranger, task) is False
    assert TaskAuthorizationService.can_complete(stranger, task) is False


def test_stranger_still_cannot_complete_an_unassigned_task() -> None:
    owner = build_user()
    stranger = build_user()
    # Sanity check: a random authenticated user must not be able to complete
    # a task merely because it happens to be unassigned (assigned_to is None
    # must never be treated as a wildcard match).
    task = build_task(owner_id=owner.id, assigned_to=None)

    assert stranger.id != owner.id
    assert task.assigned_to is None
    assert TaskAuthorizationService.can_complete(stranger, task) is False
    assert TaskAuthorizationService.can_complete(build_user(id=uuid4()), task) is False
