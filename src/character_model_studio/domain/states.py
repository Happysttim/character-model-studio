"""Persistent reconstruction-attempt state machine."""

from __future__ import annotations

from enum import StrEnum


class AttemptStatus(StrEnum):
    CREATED = "CREATED"
    PREPROCESSING = "PREPROCESSING"
    RECONSTRUCTING = "RECONSTRUCTING"
    TEXTURING = "TEXTURING"
    VALIDATING_MODEL = "VALIDATING_MODEL"
    READY_FOR_REVIEW = "READY_FOR_REVIEW"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


ALLOWED_TRANSITIONS: dict[AttemptStatus, frozenset[AttemptStatus]] = {
    AttemptStatus.CREATED: frozenset({AttemptStatus.PREPROCESSING, AttemptStatus.CANCELLED}),
    AttemptStatus.PREPROCESSING: frozenset(
        {AttemptStatus.RECONSTRUCTING, AttemptStatus.CANCELLED, AttemptStatus.FAILED}
    ),
    AttemptStatus.RECONSTRUCTING: frozenset(
        {
            AttemptStatus.TEXTURING,
            AttemptStatus.VALIDATING_MODEL,
            AttemptStatus.CANCELLED,
            AttemptStatus.FAILED,
        }
    ),
    AttemptStatus.TEXTURING: frozenset(
        {AttemptStatus.VALIDATING_MODEL, AttemptStatus.CANCELLED, AttemptStatus.FAILED}
    ),
    AttemptStatus.VALIDATING_MODEL: frozenset(
        {AttemptStatus.READY_FOR_REVIEW, AttemptStatus.CANCELLED, AttemptStatus.FAILED}
    ),
    AttemptStatus.READY_FOR_REVIEW: frozenset({AttemptStatus.ACCEPTED, AttemptStatus.REJECTED}),
    AttemptStatus.ACCEPTED: frozenset(),
    AttemptStatus.REJECTED: frozenset(),
    AttemptStatus.FAILED: frozenset(),
    AttemptStatus.CANCELLED: frozenset(),
}


def can_transition(current: AttemptStatus, target: AttemptStatus) -> bool:
    """Return whether an attempt-state transition is valid."""
    return target in ALLOWED_TRANSITIONS[current]
