"""Agent comparator: pairwise comparison with statistical significance.

Provides pairwise comparison of agents, strength/weakness analysis,
and confidence intervals with p-values for determining whether
differences are statistically significant.
"""

from __future__ import annotations

import logging
import math
from typing import TYPE_CHECKING

from agent33.evaluation.comparative.models import (
    AgentProfile,
    ComparisonOutcome,
    ComparisonResult,
)
from agent33.evaluation.comparative.percentile import PercentileCalculator

if TYPE_CHECKING:
    from agent33.evaluation.comparative.population import PopulationTracker

logger = logging.getLogger(__name__)

# Threshold below which a score difference is considered a draw
DEFAULT_DRAW_THRESHOLD = 0.01

# Default confidence level for statistical significance testing
DEFAULT_CONFIDENCE_LEVEL = 0.95

# Percentile thresholds for strength/weakness classification
STRENGTH_THRESHOLD = 75.0
WEAKNESS_THRESHOLD = 25.0


class AgentComparator:
    """Compare agents within a population and determine statistical significance.

    Uses the population tracker's data to perform pairwise comparisons,
    generate agent profiles with strengths/weaknesses, and assess statistical
    significance of differences.
    """

    def __init__(
        self,
        population: PopulationTracker,
        draw_threshold: float = DEFAULT_DRAW_THRESHOLD,
        confidence_level: float = DEFAULT_CONFIDENCE_LEVEL,
    ) -> None:
        self._population = population
        self._draw_threshold = draw_threshold
        self._confidence_level = confidence_level

    def compare_agents(
        self,
        agent_a: str,
        agent_b: str,
        metric_name: str,
    ) -> ComparisonResult | None:
        """Compare two agents on a specific metric.

        Returns ``None`` if either agent has no data for the metric.

        Parameters
        ----------
        agent_a:
            Name of the first agent.
        agent_b:
            Name of the second agent.
        metric_name:
            The metric to compare on.

        Returns
        -------
        ComparisonResult or None
            The pairwise comparison result, or None if data is missing.
        """
        score_a = self._population.get_agent_mean(agent_a, metric_name)
        score_b = self._population.get_agent_mean(agent_b, metric_name)

        if score_a is None or score_b is None:
            return None

        margin = score_a - score_b
        abs_margin = abs(margin)

        if abs_margin <= self._draw_threshold:
            outcome = ComparisonOutcome.DRAW
        elif margin > 0:
            outcome = ComparisonOutcome.WIN
        else:
            outcome = ComparisonOutcome.LOSS

        # Statistical significance via Welch's approximate t-test
        p_value = self._compute_p_value(agent_a, agent_b, metric_name)
        significant = p_value is not None and p_value < (1.0 - self._confidence_level)

        return ComparisonResult(
            agent_a=agent_a,
            agent_b=agent_b,
            metric_name=metric_name,
            score_a=round(score_a, 6),
            score_b=round(score_b, 6),
            outcome=outcome,
            margin=round(abs_margin, 6),
            statistically_significant=significant,
            p_value=round(p_value, 6) if p_value is not None else None,
            confidence_level=self._confidence_level,
        )

    def compare_all_metrics(
        self,
        agent_a: str,
        agent_b: str,
    ) -> list[ComparisonResult]:
        """Compare two agents across all tracked metrics.

        Parameters
        ----------
        agent_a:
            Name of the first agent.
        agent_b:
            Name of the second agent.

        Returns
        -------
        list[ComparisonResult]
            Comparison results for each metric where both agents have data.
        """
        results: list[ComparisonResult] = []
        for metric in self._population.metric_names:
            result = self.compare_agents(agent_a, agent_b, metric)
            if result is not None:
                results.append(result)
        return results

    def build_agent_profile(
        self,
        agent_name: str,
        elo_rating: float = 1500.0,
    ) -> AgentProfile:
        """Build a comprehensive comparative profile for an agent.

        The profile includes percentile ranks per metric, identification of
        strengths and weaknesses, and overall standing within the population.

        Parameters
        ----------
        agent_name:
            The agent to profile.
        elo_rating:
            The agent's current Elo rating.

        Returns
        -------
        AgentProfile
            The agent's comparative profile.
        """
        metric_percentiles: dict[str, float] = {}
        strengths: list[str] = []
        weaknesses: list[str] = []

        for metric in self._population.metric_names:
            means = self._population.get_population_means(metric)
            agent_mean = means.get(agent_name)
            if agent_mean is None:
                continue

            # Compute percentile rank within the population
            percentile_ranks = PercentileCalculator.compute_percentile_ranks(means)
            pct = percentile_ranks.get(agent_name, 50.0)
            metric_percentiles[metric] = round(pct, 2)

            if pct >= STRENGTH_THRESHOLD:
                strengths.append(metric)
            elif pct <= WEAKNESS_THRESHOLD:
                weaknesses.append(metric)

        # Overall percentile is the mean of per-metric percentiles
        if metric_percentiles:
            overall_pct = sum(metric_percentiles.values()) / len(metric_percentiles)
        else:
            overall_pct = 0.0

        # Determine trend from Elo history or fallback to stable
        trend = "stable"

        total_evals = self._population.get_agent_scores_count(agent_name)

        return AgentProfile(
            agent_name=agent_name,
            elo_rating=elo_rating,
            overall_percentile=round(overall_pct, 2),
            total_evaluations=total_evals,
            strengths=strengths,
            weaknesses=weaknesses,
            metric_percentiles=metric_percentiles,
            recent_trend=trend,
        )

    def _compute_p_value(
        self,
        agent_a: str,
        agent_b: str,
        metric_name: str,
    ) -> float | None:
        """Compute an approximate p-value using Welch's t-test.

        Requires at least 2 score records per agent for variance estimation.

        Returns ``None`` if there is insufficient data.
        """
        scores_map = self._population._scores.get(metric_name, {})
        samples_a = scores_map.get(agent_a, [])
        samples_b = scores_map.get(agent_b, [])

        if len(samples_a) < 2 or len(samples_b) < 2:
            return None

        n_a = len(samples_a)
        n_b = len(samples_b)
        mean_a = sum(samples_a) / n_a
        mean_b = sum(samples_b) / n_b

        var_a = sum((x - mean_a) ** 2 for x in samples_a) / (n_a - 1)
        var_b = sum((x - mean_b) ** 2 for x in samples_b) / (n_b - 1)

        se = math.sqrt(var_a / n_a + var_b / n_b)
        if se < 1e-12:
            # Zero variance on both sides: either identical or effectively zero difference
            return 1.0 if abs(mean_a - mean_b) < 1e-12 else 0.0

        t_stat = abs(mean_a - mean_b) / se

        # Welch-Satterthwaite degrees of freedom
        num = (var_a / n_a + var_b / n_b) ** 2
        denom_a = (var_a / n_a) ** 2 / (n_a - 1) if n_a > 1 else 0.0
        denom_b = (var_b / n_b) ** 2 / (n_b - 1) if n_b > 1 else 0.0
        denom = denom_a + denom_b
        if denom < 1e-12:
            return None
        df = num / denom

        # Approximate two-tailed p-value using a standard normal approximation
        # for large df. For small df, this is conservative but acceptable
        # without scipy dependency.
        p_value = self._normal_survival(t_stat, df)
        return p_value

    @staticmethod
    def _normal_survival(t: float, df: float) -> float:
        """Approximate two-tailed p-value from a t-statistic.

        Uses the normal approximation for t-distribution when df is
        moderate-to-large. For small df, applies a simple correction.
        This avoids a scipy dependency.
        """
        # Adjust t for small degrees of freedom (Bartlett's approximation)
        if df < 30:
            correction = 1.0 + 1.0 / (4.0 * max(df, 1.0))
            t = t / correction

        # Standard normal CDF approximation (Abramowitz & Stegun 26.2.17)
        x = t / math.sqrt(2.0)
        # erfc approximation using the complementary error function
        a = abs(x)
        # Rational approximation for erfc
        p = 0.3275911
        a1 = 0.254829592
        a2 = -0.284496736
        a3 = 1.421413741
        a4 = -1.453152027
        a5 = 1.061405429
        t_val = 1.0 / (1.0 + p * a)
        erfc_approx = (
            a1 * t_val + a2 * t_val**2 + a3 * t_val**3 + a4 * t_val**4 + a5 * t_val**5
        ) * math.exp(-(a**2))
        # Two-tailed p-value
        return min(1.0, max(0.0, erfc_approx))
