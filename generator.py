import pandas as pd
from ctgan import CTGAN


def generate_synthetic_data(
    df: pd.DataFrame, num_samples: int = 100, epochs: int = 20
) -> pd.DataFrame:
    discrete_columns = list(
        df.select_dtypes(include=["object", "category"]).columns
    )
    synthesizer = CTGAN(epochs=epochs, verbose=False)
    synthesizer.fit(df, discrete_columns)
    synthetic_df = synthesizer.sample(num_samples)
    return synthetic_df