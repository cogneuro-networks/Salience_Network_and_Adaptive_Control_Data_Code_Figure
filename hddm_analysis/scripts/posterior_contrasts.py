"""Posterior contrast decomposition for group-level HDDM parameters."""

from __future__ import annotations

import itertools
from itertools import combinations
from typing import Dict, List, Tuple

import arviz as az
import numpy as np


def get_node_value(data, param: str, condition_str: str) -> np.ndarray:
    """Return MCMC draws for a group-level parameter node."""
    if isinstance(data, az.InferenceData):
        return data.posterior[f"{param}({condition_str})"].values.flatten()
    return data.nodes_db.node[f"{param}({condition_str})"].trace()


def calculate_effect(
    values: np.ndarray, ci_percentiles: Tuple[float, float] = (2.5, 97.5)
) -> dict:
    """Posterior mean and equal-tailed credible interval for a contrast."""
    return {
        "mean": float(np.mean(values)),
        "ci_lower": float(np.percentile(values, ci_percentiles[0])),
        "ci_upper": float(np.percentile(values, ci_percentiles[1])),
    }


def flexible_trace_analysis(
    data,
    param: str,
    factors: Dict[str, List[str]],
    separator: str = ".",
    verbose: bool = False,
) -> Dict[str, dict]:
    """
    Decompose posterior traces into main effects, interactions, and simple effects.

    Reference levels for dummy-coded interactions are the last level listed for
    each factor in ``factors``.
    """
    factor_names = list(factors.keys())
    all_conditions = []
    for values in np.ndindex(*[len(levels) for levels in factors.values()]):
        condition = []
        for factor_idx, value_idx in enumerate(values):
            condition.append(factors[factor_names[factor_idx]][value_idx])
        all_conditions.append(separator.join(condition))

    traces = {}
    for condition in all_conditions:
        traces[condition] = get_node_value(data, param, condition)
        if verbose:
            t = traces[condition]
            print(
                f"condition: {condition}, mean: {np.mean(t):.4f}, "
                f"sd: {np.std(t):.4f}, "
                f"95% CI: {np.percentile(t, 2.5):.4f} to {np.percentile(t, 97.5):.4f}"
            )

    results: Dict[str, dict] = {}

    for factor_idx, (factor_name, levels) in enumerate(factors.items()):
        if len(levels) < 2:
            continue

        level_means = {}
        for level in levels:
            level_traces = []
            for condition, trace in traces.items():
                if condition.split(separator)[factor_idx] == level:
                    level_traces.append(trace)
            level_means[level] = np.mean(level_traces, axis=0)

        for level1, level2 in combinations(levels, 2):
            effect_name = f"main_effect_{factor_name}_{level1}_vs_{level2}"
            results[effect_name] = calculate_effect(level_means[level1] - level_means[level2])

    processed_two_way_interactions = set()

    for n_factors in range(2, len(factors) + 1):
        for factor_combo in combinations(enumerate(factors.items()), n_factors):
            factor_indices = [idx for idx, _ in factor_combo]
            combo_factor_names = [name for _, (name, _) in factor_combo]

            if any(len(factors[name]) < 2 for name in combo_factor_names):
                continue

            interaction_name = f"interaction_{'_'.join(combo_factor_names)}"

            dummy_combinations = []
            for name in combo_factor_names:
                levels = factors[name]
                dummy_combinations.append([f"{name}_{level}" for level in levels[:-1]])

            base_condition = [factors[name][-1] for name in combo_factor_names]

            for dummy_values in itertools.product(*dummy_combinations):
                interaction_effect = np.zeros_like(list(traces.values())[0])
                if verbose:
                    print(f"factor_names: {combo_factor_names}")

                for condition, trace in traces.items():
                    condition_parts = condition.split(separator)
                    target_condition_parts = [condition_parts[i] for i in factor_indices]
                    virtual_values = []
                    for dummy_name in dummy_values:
                        dummy_factor_name = dummy_name.split("_")[0]
                        dummy_level = dummy_name.split("_")[1]
                        local_idx = combo_factor_names.index(dummy_factor_name)
                        if target_condition_parts[local_idx] == dummy_level:
                            virtual_values.append(1)
                        elif target_condition_parts[local_idx] == base_condition[local_idx]:
                            virtual_values.append(-1)
                        elif len(factors[dummy_factor_name]) > 2:
                            virtual_values.append(0)
                    if verbose:
                        print(f"condition: {condition}, virtual_values: {virtual_values}")
                    interaction_effect += np.prod(virtual_values) * trace

                interaction_key = (
                    f"{interaction_name}_{'_'.join(dummy_values)}_{'_'.join(base_condition)}"
                )
                results[interaction_key] = calculate_effect(interaction_effect)

            if n_factors == 2:
                interaction_id = tuple(sorted(combo_factor_names))
                if interaction_id in processed_two_way_interactions:
                    continue
                processed_two_way_interactions.add(interaction_id)

                factor_a_name, factor_b_name = combo_factor_names
                factor_a_levels = factors[factor_a_name]
                factor_b_levels = factors[factor_b_name]
                factor_a_idx, factor_b_idx = factor_indices

                for level_a in factor_a_levels:
                    level_b_traces = {}
                    for level_b in factor_b_levels:
                        selected_traces = []
                        for condition, trace in traces.items():
                            parts = condition.split(separator)
                            if parts[factor_a_idx] == level_a and parts[factor_b_idx] == level_b:
                                selected_traces.append(trace)
                        if selected_traces:
                            level_b_traces[level_b] = np.mean(selected_traces, axis=0)

                    if len(level_b_traces) >= 2:
                        for level_b1, level_b2 in combinations(level_b_traces.keys(), 2):
                            key = (
                                f"simple_effect_{factor_b_name}_{level_b1}_vs_{level_b2}"
                                f"_at_{factor_a_name}_{level_a}"
                            )
                            results[key] = calculate_effect(
                                level_b_traces[level_b1] - level_b_traces[level_b2]
                            )

                for level_b in factor_b_levels:
                    level_a_traces = {}
                    for level_a in factor_a_levels:
                        selected_traces = []
                        for condition, trace in traces.items():
                            parts = condition.split(separator)
                            if parts[factor_a_idx] == level_a and parts[factor_b_idx] == level_b:
                                selected_traces.append(trace)
                        if selected_traces:
                            level_a_traces[level_a] = np.mean(selected_traces, axis=0)

                    if len(level_a_traces) >= 2:
                        for level_a1, level_a2 in combinations(level_a_traces.keys(), 2):
                            key = (
                                f"simple_effect_{factor_a_name}_{level_a1}_vs_{level_a2}"
                                f"_at_{factor_b_name}_{level_b}"
                            )
                            results[key] = calculate_effect(
                                level_a_traces[level_a1] - level_a_traces[level_a2]
                            )

    if all(name in factors for name in ["prob", "duration", "transition"]):
        prob_levels = factors["prob"]
        duration_levels = factors["duration"]
        transition_levels = factors["transition"]
        if len(prob_levels) >= 2 and len(transition_levels) >= 2:
            idx_prob = list(factors.keys()).index("prob")
            idx_duration = list(factors.keys()).index("duration")
            idx_transition = list(factors.keys()).index("transition")

            for d in duration_levels:

                def collect(level_prob, level_trans, duration=d):
                    selected = []
                    for condition, trace in traces.items():
                        parts = condition.split(separator)
                        if (
                            parts[idx_duration] == duration
                            and parts[idx_prob] == level_prob
                            and parts[idx_transition] == level_trans
                        ):
                            selected.append(trace)
                    return np.mean(selected, axis=0) if selected else None

                p1t1 = collect(prob_levels[0], transition_levels[0])
                p1t2 = collect(prob_levels[0], transition_levels[1])
                p2t1 = collect(prob_levels[1], transition_levels[0])
                p2t2 = collect(prob_levels[1], transition_levels[1])

                if all(x is not None for x in (p1t1, p1t2, p2t1, p2t2)):
                    key = f"simple_interaction_prob_transition_at_duration_{d}"
                    results[key] = calculate_effect((p1t1 - p1t2) - (p2t1 - p2t2))

                if p1t1 is not None and p1t2 is not None:
                    key = f"simple_main_transition_at_prob_{prob_levels[0]}_duration_{d}"
                    results[key] = calculate_effect(p1t1 - p1t2)
                if p2t1 is not None and p2t2 is not None:
                    key = f"simple_main_transition_at_prob_{prob_levels[1]}_duration_{d}"
                    results[key] = calculate_effect(p2t1 - p2t2)

    return results


def results_to_rows(results: Dict[str, dict], param: str, model: str) -> List[dict]:
    """Flatten contrast dict into CSV-friendly rows."""
    rows = []
    for effect_name, stats in sorted(results.items()):
        effect_type = effect_name.split("_", 1)[0]
        if effect_name.startswith("simple_interaction") or effect_name.startswith("simple_main"):
            effect_type = "simple_followup"
        elif effect_name.startswith("simple_effect"):
            effect_type = "simple_effect"
        elif effect_name.startswith("interaction"):
            effect_type = "interaction"
        elif effect_name.startswith("main_effect"):
            effect_type = "main_effect"
        rows.append(
            {
                "model": model,
                "parameter": param,
                "effect_type": effect_type,
                "effect": effect_name,
                **stats,
            }
        )
    return rows
