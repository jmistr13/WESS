#df_customMethods - Logan
import pandas as pd
import numpy as np
import os

# function to send csv string to other programs.
# Replace string with desired csv path
def csv_path():
    return 'DataAnalysis/appDev/test_data.csv.csv' #for windows
    #return 'data2.csv' #for linux

def loadAndProcessData(filename):
    this_df = pd.read_csv(filename, usecols=['sensorName', 'lat', 'long', 'transmitDateTime', 'CO', 'NH3', 'NO2', 'TDS', 'turbidity'],
                          comment='#', parse_dates=['transmitDateTime'])  # <-- Ensure datetime parsing

    #print("Before Processing:", this_df.shape)  # Debugging

    # Check if parsing worked
    print(this_df.dtypes)  # Should show 'transmitDateTime' as datetime64[ns]

    #df_new = mostRecentValidLoc(this_df)  # Check if this function is filtering too much
    #print("After mostRecentValidLoc:", df_new.shape)  # Debugging

    #df_new.to_csv('newdata.csv', index=False)  # Save to inspect

    return this_df


def updateMainDf(filename):
    df = pd.read_csv(filename, usecols=['sensorName', 'lat', 'long', 'transmitDateTime', 'CO', 'NH3', 'NO2', 'TDS', 'turbidity'],
                     comment='#')

def mostRecentValidLoc (df: pd.DataFrame):
    """
    Takes in a dataframe with multiple readings per sensor and returns a dataframe
    with the most recent reading per sensor that also has a valid lat and long
    :param df:
    :return df:
    """
    df_new = df.dropna(how='all')
    df_new = df_new.sort_values(by=['sensorName', 'transmitDateTime'], ascending=False)

    # Forward fill missing lat and long values within each sensorName group
    df_new.replace('', np.nan, inplace=True) #Just in case fillna has already been run, turn empty strigns back to nan so ffill works
    df_new['lat'] = df_new['lat'].ffill()
    df_new['long'] = df_new['long'].ffill()

    df_new = df_new.dropna(subset=['lat','long'])  # The most recent reading for a sensor has filtered it's location down, so dropping removes recent readings that are missing location
    df_new = df_new.drop_duplicates(subset=['sensorName'], keep='first')  # Dropping duplicate sensor readings

    return df_new

def mostRecentInheritLoc (df: pd.DataFrame):
    """
    Takes in a dataframe with multiple readings per sensor and returns a dataframe that
    has the most recent reading per sensor, regardless of having valid lat and long.
    Will inherit most recent lat and long available for the same sensorName
    :param df:
    :return df:
    """
    df_new = df.dropna(how='all')
    df_new = df_new.sort_values(by=['sensorName', 'transmitDateTime'], ascending=True)

    # Forward fill missing lat and long values within each sensorName group
    df_new.replace('', np.nan, inplace=True) #Just in case fillna has already been run, turn empty strigns back to nan so ffill works
    df_new['lat'] = df_new['lat'].ffill()
    df_new['long'] = df_new['long'].ffill()

    df_new = df_new.drop_duplicates(subset=['sensorName'], keep='last')  # Dropping duplicate sensor readings

    return df_new

def get_csv_modified_time(filename):
    return os.path.getmtime(filename)