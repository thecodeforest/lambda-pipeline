import pandas as pd
import pandera as pa
from typing import Tuple
import yaml
from pathlib import Path


with open(Path(__file__).parent.parent / "conf.yaml") as f:
    conf = yaml.load(f, Loader=yaml.FullLoader)


def validate_weather_df(df: pd.DataFrame) -> Tuple[bool, pd.DataFrame]:
    """Validate weather data using pandera schema."""
    cities = conf.get('cities')
    schema = pa.DataFrameSchema(
        {

            "temperature": pa.Column(pa.Float, pa.Check.ge(0)),
            "humidity": pa.Column(pa.Float, pa.Check.ge(0)),
            "description": pa.Column(pa.String, checks=pa.Check(lambda x: len(x) < 100, element_wise=True)),
            "city": pa.Column(pa.String, checks=pa.Check.isin(cities)),
        },
        coerce=True
    )

    try:
        schema.validate(df)
        return True, None
    except pa.errors.SchemaError as err:
        return False, err.failure_cases
