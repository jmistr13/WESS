import pandas as pd

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
    df_new['lat'] = df_new['lat'].ffill()
    df_new['long'] = df_new['long'].ffill()

    df_new = df_new.drop_duplicates(subset=['sensorName'], keep='last')  # Dropping duplicate sensor readings

    return df_new
