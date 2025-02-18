import pandas as pd

df = pd.read_csv('nova.csv', usecols=['Date & Time', 'Pollutant', 'Unit', 'Station', 'Average'], comment='#')
df.dropna(subset=['Average'])
print(df['Average'].mean())
