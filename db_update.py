import numpy as np
import pandas as pd
import sqlite3
from file_read_backwards import FileReadBackwards
from contextlib import closing

temp_files = ['sisalla', 'ulkona', 'jarvessa', 'kellarissa', 'rauhalassa', 'saunassa', 'lampo_roykka']

data_folder = '/var/www/html/nuottis/data/'
#data_folder = 'lampotilat/data/'
path = '/home/pi/serveri/lampotilat_app/lampotilat/'
#path = ''

def load_data(filename, last_measurement):
    data = []
    with FileReadBackwards(filename, encoding="utf-8") as File:
        for line in File:
            fields=line.split(',')
            epoch=fields[0][0:10]
            if len(epoch)==10:
                if int(epoch)<last_measurement:
                    break
                data.append([epoch, fields[1]])

    df = pd.DataFrame(data, columns = ['epoch', 'data'])
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

def load_dataset():
    with closing(sqlite3.connect(path+'db.sqlite3')) as connection:
        with closing(connection.cursor()) as cursor:
            last_measurement=cursor.execute('SELECT MAX(date) FROM lampotilat_temperature').fetchone()[0]
            if last_measurement==None:
                last_measurement=0
            else:
                cursor.execute('DELETE FROM lampotilat_temperature WHERE date=?', (last_measurement,))
                connection.commit()

#            print(last_measurement)
            data=[]
            for file in temp_files:
                data.append(load_tempdata(data_folder+file+'.csv', last_measurement))
            data.append(load_winddata(data_folder+'tuuli.csv', last_measurement))
            data.append(load_raindata(data_folder+'sade.csv', last_measurement))
            data.append(load_movedata(data_folder+'liike.csv', last_measurement))
            data.append(load_snowdata(data_folder+'lumi_roykka.csv', last_measurement))
            df = pd.concat(data, axis=1)
            df = df.groupby(pd.Grouper(freq='H')).mean()
            df = df.sort_values('date')
            records = df.to_records()
#            print(len(records))
            for record in records:
                data=(int(record[0].astype('datetime64[s]').astype('int')),record[1],record[2],record[3],record[4],record[5],record[6],record[7],record[8],record[9],record[10],record[11],record[12])
                cursor.execute(
                    'INSERT INTO lampotilat_temperature (date, Sisalla, Ulkona, Jarvessa, Kellarissa, Rauhalassa, Saunassa, Roykassa, Tuuli, Tuulimax, Sade, Liike, Lumi) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)', 
                    data
                )
            connection.commit()
load_dataset()

