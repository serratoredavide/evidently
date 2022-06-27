from dataclasses import dataclass
from typing import Optional, Tuple, List

import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error

from evidently import ColumnMapping
from evidently.analyzers.regression_performance_analyzer import RegressionPerformanceAnalyzer

from evidently.v2.metrics.base_metric import InputData
from evidently.v2.metrics.base_metric import Metric


@dataclass
class RegressionPerformanceMetricsResults:
    mean_error: float
    me_distr: List[Tuple[object, float]]
    ref_me_distr: Optional[List[Tuple[object, float]]]
    mean_abs_error: float
    mae_distr: List[Tuple[object, float, int]]
    ref_mae_distr: Optional[List[Tuple[object, float, int]]]
    mean_abs_perc_error: float
    abs_error_max: float
    error_std: float
    abs_error_std: float
    abs_perc_error_std: float
    error_normality: dict
    underperformance: dict
    error_bias: Optional[dict] = None


class RegressionPerformanceMetrics(Metric[RegressionPerformanceMetricsResults]):
    def __init__(self):
        self.analyzer = RegressionPerformanceAnalyzer()

    def calculate(self, data: InputData, metrics: dict) -> RegressionPerformanceMetricsResults:
        if data.current_data is None:
            raise ValueError("current dataset should be present")

        if data.reference_data is None:
            analyzer_results = self.analyzer.calculate(
                reference_data=data.current_data,
                current_data=None,
                column_mapping=data.column_mapping
            )
        else:
            analyzer_results = self.analyzer.calculate(
                reference_data=data.reference_data,
                current_data=data.current_data,
                column_mapping=data.column_mapping
            )

        me_distr, mae_distr = _me_mae_distr(data.current_data, data.column_mapping)
        ref_me_distr, ref_mae_distr = _me_mae_distr(data.reference_data, data.column_mapping)\
            if data.reference_data is not None else (None, None)

        return RegressionPerformanceMetricsResults(
            mean_error=analyzer_results.reference_metrics.mean_error,
            me_distr=me_distr,
            ref_me_distr=ref_me_distr,
            mean_abs_error=analyzer_results.reference_metrics.mean_abs_error,
            mae_distr=mae_distr,
            ref_mae_distr=ref_mae_distr,
            mean_abs_perc_error=analyzer_results.reference_metrics.mean_abs_perc_error,
            abs_error_max=analyzer_results.reference_metrics.abs_error_max,
            error_std=analyzer_results.reference_metrics.error_std,
            abs_error_std=analyzer_results.reference_metrics.abs_error_std,
            abs_perc_error_std=analyzer_results.reference_metrics.abs_perc_error_std,
            error_normality=analyzer_results.reference_metrics.error_normality,
            underperformance=analyzer_results.reference_metrics.underperformance,
            error_bias=analyzer_results.error_bias
        )


def _me_mae_distr(df: pd.DataFrame, column_mapping: ColumnMapping):
    df = df.copy()
    df['target_binned'] = pd.cut(df[column_mapping.target], 10)

    data = df[column_mapping.target] - df[column_mapping.prediction]
    me_bins = np.histogram_bin_edges(data, bins="doane")
    me_hist = np.histogram(data, bins=me_bins)

    mae = df.groupby('target_binned').apply(lambda x: mean_absolute_error(x.target, x.preds))
    mae_hist = df.target_binned.value_counts().sort_index()
    return ([(y, x) for x, y in zip(me_hist[0], me_hist[1])],
            [(idx, mae[idx], value) for idx, value in mae_hist.items()])
