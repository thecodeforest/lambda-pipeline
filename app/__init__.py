import os
from datetime import datetime
import pandas as pd
import awswrangler as wr
from utils.weather import (get_weather,
                           extract_weather_data,
                           convert_celcius_to_fahrenheit)


output_bucket = os.environ["OUTPUT_BUCKET"]
openweather_api_key = os.environ["OPENWEATHER_API_KEY"]


def weather_collector(event, context):
    """Lambda function to retrieve weather data from openweathermap api. 
    The data is then stored in a S3 bucket as a CSV file. Note you will need 
    to create an openweathermap account and get an API key to use this function.
    """

    all_data = pd.DataFrame()
    cities = ['New York', 'Portland', 'Chicago', 'Seattle', 'Dallas']
    columns = ['temperature', 'humidity', 'description', 'city']
    for city in cities:
        data = get_weather(city=city, api_key=openweather_api_key)
        if data:
            data_fmt = extract_weather_data(data) + [city]
            weather_df = pd.DataFrame([data_fmt],
                                      columns=columns,
                                      index=[0]
                                      )
            all_data = pd.concat([all_data, weather_df], axis=0)
    # convert temperature to fahrenheit
    all_data['temperature'] = all_data['temperature'].apply(
        convert_celcius_to_fahrenheit)
    # save to s3
    now = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
    wr.s3.to_csv(df=all_data,
                 path=f"s3://{output_bucket}/weather_data_{now}.csv",
                 index=False
                 )
