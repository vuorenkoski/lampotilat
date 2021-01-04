from .models import Temperature
import numpy as np
import pandas as pd

timezone = 'Europe/Helsinki'

def load_data(filename, last_measurement):
    df = pd.read_csv(filename, sep=',', warn_bad_lines=False, error_bad_lines=False, dtype=str)
    df.columns = ['epoch', 'data']
    df = df[df['epoch'].str.len()<15]
    df['epoch'] = df['epoch'].str[0:-3]
    df = df[df['epoch'].astype(int)>last_measurement]
    df['date'] = pd.to_datetime(df['epoch'], unit='s')
    df[filename] = pd.to_numeric(df['data'], errors='coerce')
    df = df.set_index('date').drop(columns=['epoch', 'data'])
    df = df[~df.index.duplicated(keep='first')]
    return df

def load_tempdata(filename, last_measurement):
    df = load_data(filename, last_measurement)
    df = df[df[filename]<50]
    df = df[df[filename]>-50]
    return df

def load_raindata(filename, last_measurement):
    df = load_data(filename, last_measurement)
    df = df[df[filename]<1000]
    return df

def load_winddata(filename, last_measurement):
    df = load_data(filename, last_measurement)
    df = df[df[filename]<1000]
    df = df.groupby(pd.Grouper(freq='H')).agg({filename: ['mean', 'max']})
    return df

def load_snowdata(filename, last_measurement):
    df = load_data(filename, last_measurement)
    df = df[df[filename]<200]
    return df

def load_movedata(filename, last_measurement):
    df = pd.read_csv(filename, sep=',', warn_bad_lines=False, error_bad_lines=False, dtype=str)
    df.columns = ['epoch']
    df = df[df['epoch'].str.len()<15]
    df['epoch'] = df['epoch'].str[0:-3]
    df = df[df['epoch'].astype(int)>last_measurement]
    df[filename] = 1
    df['date'] = pd.to_datetime(df['epoch'], unit='s')
    df = df.set_index('date').drop(columns=['epoch'])
    df = df[~df.index.duplicated(keep='first')]

    df = df.groupby(pd.Grouper(freq='H')).sum()
    return df

def load_dataset(last_measurement, csv_files, data_folder):
    data=[]
    for file in csv_files:
        data.append(load_tempdata(data_folder+file+'.csv', last_measurement))
    print("lmäpötilat ladattu")
    data.append(load_winddata(data_folder+'tuuli.csv', last_measurement))
    print("tuuli ladattu")
    data.append(load_raindata(data_folder+'sade.csv', last_measurement))
    print("sade ladattu")
    data.append(load_movedata(data_folder+'liike.csv', last_measurement))
    print("liike ladattu")
    data.append(load_snowdata(data_folder+'lumi_roykka.csv', last_measurement))
    print("lumi ladattu")
    df = pd.concat(data, axis=1)
    print("yhdistetty")
    df = df.groupby(pd.Grouper(freq='H')).mean()
    df = df.sort_values('date')
#    df.to_csv(data_folder+'yhdistetty.csv', sep=',', float_format='%.1f')
    records = df.to_records()
    for record in records:
        temperature = Temperature(
            date = record[0].astype('datetime64[s]').astype('int'),
            Sisalla = record[1], 
            Ulkona = record[2], 
            Jarvessa = record[3], 
            Kellarissa = record[4],
            Rauhalassa = record[5], 
            Saunassa = record[6], 
            Roykassa = record[7],
            Tuuli = record[8],
            Tuulimax = record[9], 
            Sade = record[10], 
            Liike = record[11],
            Lumi = record[12],
        )
        temperature.save()
