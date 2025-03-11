import pandas as pd
df = pd.read_csv('data.csv', usecols=['sensorName', 'lat', 'long', 'transmitDate', 'transmitHour', 'CO', 'NH3', 'NO2', 'TDS', 'turbidity'],
                 comment='#')

df.insert(loc=3, column='transmitDateTime', value=pd.to_datetime(df['transmitDate'] + ' ' + df['transmitHour'].astype(str)))
df.drop('transmitDate', axis=1, inplace=True)
df.drop('transmitHour', axis=1, inplace=True)
df.to_csv('data.csv', index=False)