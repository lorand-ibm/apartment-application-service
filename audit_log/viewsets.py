from contextlib import contextmanager
from copy import copy
from django.contrib.auth.models import AnonymousUser
from django.db import transaction
from django.db.models import Model
from rest_framework.exceptions import NotAuthenticated, PermissionDenied
from rest_framework.viewsets import ModelViewSet
from typing import Optional, Union

from audit_log import audit_logging
from audit_log.enums import Operation, Status
from users.models import Profile


class AuditLoggingModelViewSet(ModelViewSet):
    method_to_operation = {
        "POST": Operation.CREATE,
        "GET": Operation.READ,
        "PUT": Operation.UPDATE,
        "PATCH": Operation.UPDATE,
        "DELETE": Operation.DELETE,
    }
    created_instance: Optional[Model] = None

    def permission_denied(self, request, message=None, code=None):
        audit_logging.log(
            self._get_actor(),
            self._get_operation(),
            self._get_target(),
            Status.FORBIDDEN,
        )
        super().permission_denied(request, message, code)

    def retrieve(self, request, *args, **kwargs):
        with self.record_action():
            return super().retrieve(request, *args, **kwargs)

    def perform_create(self, serializer):
        with self.record_action():
            super().perform_create(serializer)
            self.created_instance = serializer.instance

    def perform_update(self, serializer):
        with self.record_action():
            super().perform_update(serializer)

    def perform_destroy(self, instance):
        target = copy(instance)  # Will be destroyed, so we must save it
        with self.record_action(target=target):
            super().perform_destroy(instance)

    @contextmanager
    def record_action(self, target: Optional[Model] = None):
        """
        This context manager will run the managed code in a transaction and writes
        a new audit log entry in the same transaction. If an exception is raised,
        the transaction will be rolled back. If the user has no permission to perform
        the given action, a "FORBIDDEN" audit log event will be recorded.
        """
        actor = copy(self._get_actor())  # May be destroyed if actor is also the target
        operation = self._get_operation()
        try:
            with transaction.atomic():
                yield
                audit_logging.log(
                    actor,
                    operation,
                    target or self._get_target(),
                    Status.SUCCESS,
                )
        except (NotAuthenticated, PermissionDenied):
            audit_logging.log(
                actor,
                operation,
                target or self._get_target(),
                Status.FORBIDDEN,
            )
            raise

    def _get_actor(self) -> Union[Profile, AnonymousUser]:
        return getattr(self.request.user, "profile", self.request.user)

    def _get_operation(self) -> Operation:
        return self.method_to_operation[self.request.method]

    def _get_target(self) -> Optional[Model]:
        target = None
        lookup_value = self.kwargs.get(self.lookup_field, None)
        if lookup_value is not None:
            target = self.queryset.model.objects.filter(
                **{self.lookup_field: lookup_value}
            ).first()
        return target or self.created_instance or self.queryset.model()
