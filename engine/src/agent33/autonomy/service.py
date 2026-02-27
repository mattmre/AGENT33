"""Autonomy budget service — CRUD, lifecycle, and enforcement orchestration."""

from __future__ import annotations

import logging

from agent33.autonomy.enforcement import RuntimeEnforcer
from agent33.autonomy.models import (
    AutonomyBudget,
    BudgetState,
    EscalationRecord,
)
from agent33.autonomy.preflight import PreflightChecker, PreflightReport

logger = logging.getLogger(__name__)

# Valid state transitions for budget lifecycle
_VALID_TRANSITIONS: dict[BudgetState, frozenset[BudgetState]] = {
    BudgetState.DRAFT: frozenset({BudgetState.PENDING_APPROVAL, BudgetState.ACTIVE}),
    BudgetState.PENDING_APPROVAL: frozenset(
        {
            BudgetState.ACTIVE,
            BudgetState.REJECTED,
        }
    ),
    BudgetState.ACTIVE: frozenset(
        {
            BudgetState.SUSPENDED,
            BudgetState.EXPIRED,
            BudgetState.COMPLETED,
        }
    ),
    BudgetState.SUSPENDED: frozenset({BudgetState.ACTIVE, BudgetState.EXPIRED}),
    BudgetState.REJECTED: frozenset({BudgetState.DRAFT}),
    BudgetState.EXPIRED: frozenset(),
    BudgetState.COMPLETED: frozenset(),
}


class BudgetNotFoundError(Exception):
    """Raised when a budget is not found."""


class InvalidStateTransitionError(Exception):
    """Raised when a budget state transition is invalid."""

    def __init__(self, from_state: BudgetState, to_state: BudgetState) -> None:
        self.from_state = from_state
        self.to_state = to_state
        super().__init__(f"Invalid transition: {from_state.value} → {to_state.value}")


class AutonomyService:
    """Budget CRUD, lifecycle management, and enforcement orchestration."""

    def __init__(self) -> None:
        self._budgets: dict[str, AutonomyBudget] = {}
        self._enforcers: dict[str, RuntimeEnforcer] = {}
        self._escalations: dict[str, EscalationRecord] = {}
        self._checker = PreflightChecker()

    # ------------------------------------------------------------------
    # Budget CRUD
    # ------------------------------------------------------------------

    def create_budget(
        self,
        task_id: str = "",
        agent_id: str = "",
        **kwargs: object,
    ) -> AutonomyBudget:
        """Create a new autonomy budget in DRAFT state."""
        budget = AutonomyBudget(task_id=task_id, agent_id=agent_id, **kwargs)
        self._budgets[budget.budget_id] = budget
        logger.info(
            "budget_created id=%s task=%s agent=%s",
            budget.budget_id,
            task_id,
            agent_id,
        )
        return budget

    def get_budget(self, budget_id: str) -> AutonomyBudget:
        """Get a budget by ID."""
        budget = self._budgets.get(budget_id)
        if budget is None:
            raise BudgetNotFoundError(f"Budget not found: {budget_id}")
        return budget

    def list_budgets(
        self,
        state: BudgetState | None = None,
        task_id: str | None = None,
        agent_id: str | None = None,
        limit: int = 100,
    ) -> list[AutonomyBudget]:
        """List budgets with optional filters."""
        results = list(self._budgets.values())
        if state is not None:
            results = [b for b in results if b.state == state]
        if task_id is not None:
            results = [b for b in results if b.task_id == task_id]
        if agent_id is not None:
            results = [b for b in results if b.agent_id == agent_id]
        results.sort(key=lambda b: b.created_at, reverse=True)
        return results[:limit]

    def delete_budget(self, budget_id: str) -> None:
        """Delete a budget (only if in DRAFT or REJECTED state)."""
        budget = self.get_budget(budget_id)
        if budget.state not in (BudgetState.DRAFT, BudgetState.REJECTED):
            raise InvalidStateTransitionError(budget.state, BudgetState.DRAFT)
        del self._budgets[budget_id]

    # ------------------------------------------------------------------
    # Lifecycle transitions
    # ------------------------------------------------------------------

    def transition(
        self, budget_id: str, to_state: BudgetState, approved_by: str = ""
    ) -> AutonomyBudget:
        """Transition a budget to a new state."""
        budget = self.get_budget(budget_id)
        valid = _VALID_TRANSITIONS.get(budget.state, frozenset())
        if to_state not in valid:
            raise InvalidStateTransitionError(budget.state, to_state)

        budget.state = to_state
        if approved_by:
            budget.approved_by = approved_by

        logger.info(
            "budget_transition id=%s to=%s",
            budget_id,
            to_state.value,
        )
        return budget

    def activate(self, budget_id: str, approved_by: str = "") -> AutonomyBudget:
        """Activate a budget (from DRAFT or PENDING_APPROVAL)."""
        return self.transition(budget_id, BudgetState.ACTIVE, approved_by)

    def suspend(self, budget_id: str) -> AutonomyBudget:
        """Suspend an active budget."""
        return self.transition(budget_id, BudgetState.SUSPENDED)

    def complete(self, budget_id: str) -> AutonomyBudget:
        """Mark a budget as completed."""
        return self.transition(budget_id, BudgetState.COMPLETED)

    # ------------------------------------------------------------------
    # Preflight
    # ------------------------------------------------------------------

    def run_preflight(self, budget_id: str) -> PreflightReport:
        """Run preflight checks on a budget."""
        budget = self.get_budget(budget_id)
        return self._checker.check(budget)

    # ------------------------------------------------------------------
    # Enforcement
    # ------------------------------------------------------------------

    def create_enforcer(self, budget_id: str) -> RuntimeEnforcer:
        """Create a runtime enforcer for an active budget."""
        budget = self.get_budget(budget_id)
        if budget.state != BudgetState.ACTIVE:
            raise InvalidStateTransitionError(budget.state, BudgetState.ACTIVE)
        enforcer = RuntimeEnforcer(budget)
        self._enforcers[budget_id] = enforcer
        return enforcer

    def get_enforcer(self, budget_id: str) -> RuntimeEnforcer | None:
        """Get the runtime enforcer for a budget."""
        return self._enforcers.get(budget_id)

    # ------------------------------------------------------------------
    # Escalations
    # ------------------------------------------------------------------

    def list_escalations(
        self,
        budget_id: str | None = None,
        unresolved_only: bool = False,
        limit: int = 100,
    ) -> list[EscalationRecord]:
        """List escalation records."""
        # Collect from all enforcers
        all_escalations: list[EscalationRecord] = []
        for enforcer in self._enforcers.values():
            all_escalations.extend(enforcer.escalations)
        # Also include manually stored ones
        all_escalations.extend(self._escalations.values())

        if budget_id is not None:
            all_escalations = [e for e in all_escalations if e.budget_id == budget_id]
        if unresolved_only:
            all_escalations = [e for e in all_escalations if not e.resolved]
        all_escalations.sort(key=lambda e: e.created_at, reverse=True)
        return all_escalations[:limit]

    def acknowledge_escalation(self, escalation_id: str) -> bool:
        """Acknowledge an escalation."""
        for enforcer in self._enforcers.values():
            for esc in enforcer.escalations:
                if esc.escalation_id == escalation_id:
                    esc.acknowledged = True
                    return True
        esc = self._escalations.get(escalation_id)
        if esc:
            esc.acknowledged = True
            return True
        return False

    def resolve_escalation(self, escalation_id: str) -> bool:
        """Resolve an escalation."""
        for enforcer in self._enforcers.values():
            for esc in enforcer.escalations:
                if esc.escalation_id == escalation_id:
                    esc.resolved = True
                    return True
        esc = self._escalations.get(escalation_id)
        if esc:
            esc.resolved = True
            return True
        return False
