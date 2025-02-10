import pandas as pd
import numpy as np

df = pd.read_csv('data.csv', usecols=['SensorName', 'Lat', 'Long', 'TransmitDate', 'TransmitHour', 'CO', 'NH3', 'NO2'])

for row in df.itertuples():
    if(np.isnan(row[2])):
        print(f"Sensor {row[1]} has no Latitude and Longitude for reading at {row[5]} on {row[4]}")
        df.iloc[row[0], 1] = float(input("Please type latitude value: "))
        df.iloc[row[0], 2] = float(input("Please type longitude value: "))
        print()

print(df.head())
print(f"Length of data: {len(df)}")
print()
print("Saving as newdata.csv")
df.to_csv('newdata.csv', index=False)
