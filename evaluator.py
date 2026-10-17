import pandas as pd
from scipy.stats import ks_2samp


def evaluate_fidelity(real_df: pd.DataFrame, synthetic_df: pd.DataFrame) -> dict:
    """Computes Kolmogorov-Smirnov statistical similarity scores

    between numerical columns of real and synthetic datasets.
    """
    scores = {}
    numeric_cols = real_df.select_dtypes(include=["number"]).columns

    for col in numeric_cols:
        if col in synthetic_df.columns:
            res = ks_2samp(real_df[col].dropna(), synthetic_df[col].dropna())
            stat = float(res.statistic)
            p_val = float(res.pvalue)

            scores[col] = {
                "ks_statistic": round(stat, 4),
                "p_value": round(p_val, 4),
                "fidelity": "High" if p_val > 0.05 else "Moderate/Low",
            }

    return scores