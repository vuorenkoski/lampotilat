from django.http import HttpResponse
from django.shortcuts import render, redirect
from .models import Temperature
from django.db.models import Max

import numpy as np
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
from datetime import datetime
import dateutil.relativedelta

UTC2 = 2*60*60

timezone = 'Europe/Helsinki'
#data_folder = '/var/www/html/nuottis/data/'
data_folder = 'lampotilat/data/'
chart_file = 'lampotilat/static/lampotilat/chart.png'
#path = '/home/pi/serveri/lampotilat_app/lampotilat/'
path = ''
csv_files = ['sisalla', 'ulkona', 'jarvessa', 'kellarissa', 'rauhalassa', 'saunassa', 'lampo_roykka']
field_names = ['Sisalla', 'Ulkona', 'Jarvessa', 'Kellarissa', 'Rauhalassa', 'Saunassa', 'Roykassa']

def save_figure(df, kind):
    fig = df.plot(kind=kind,  figsize=(12, 5), fontsize=14).get_figure()
    fig.axes[0].legend(loc='best', fontsize=14)
    fig.axes[0].set_ylabel('lämpötila', fontsize=14)
    fig.axes[0].set_xlabel('')
    fig.axes[0].grid(axis='y')
    fig.savefig(path+chart_file)

def load_data(name, last_measurement):
    df = pd.read_csv(data_folder + name+'.csv', sep=',', warn_bad_lines=False, error_bad_lines=False, dtype=str)
    df.columns = ['epoch', 'data']
    df['epoch'] = df['epoch'].str[0:-3]
    df = df[df['epoch'].astype(int)>last_measurement]
    df['date'] = pd.to_datetime(df['epoch'], unit='s', utc=True)
    df[name] = pd.to_numeric(df['data'], errors='coerce')
    df = df.set_index('date').drop(columns=['epoch', 'data'])
    df = df.tz_convert(tz=timezone)
    df = df[df[name]<50]
    df = df[df[name]>-50]
    return df

def load_dataset(last_measurement):
    data=[]
    for file in csv_files:
        data.append(load_data(file, last_measurement))
    df = pd.concat(data)
    df = df.sort_values('date')
    df = df.groupby(pd.Grouper(freq='H')).mean()

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
        )
        temperature.save()

def setup(request):
    # Poistetaana viimeinen koska se on todennäköisesti puutteellinen
    epoch = last_measurement_epoch()
    if epoch>0:
        Measurement.objects.filter(date=epoch).delete()
    load_dataset(last_measurement_epoch())


#    df_daily = df.groupby(pd.Grouper(freq='D')).mean()
    return redirect('/')

def last_measurement_epoch():
    max=Temperature.objects.aggregate(Max('date'))['date__max']
    if max==None:
        return 0
    return max+UTC2

def index(request):
    last_measurement = 'ei dataa'
    epoch = last_measurement_epoch()
    if epoch>0:
        last_measurement = datetime.fromtimestamp(last_measurement_epoch()).strftime("%d.%m.%Y, %H:%M")
    return render(request, 'lampotilat/index.html', {'loaded': last_measurement})

def objects_to_df(model, fields, **kwargs):
    fields_wd=fields+['date']
    records = model.objects.filter(**kwargs).values_list(*fields_wd)
    df = pd.DataFrame(list(records), columns=fields_wd)
    return df

def tempchart(request):
    fields = []
    endDate = datetime.now()
    startDate = endDate - dateutil.relativedelta.relativedelta(months=1)
    vrk = False
    if request.method=="POST":
        fields.extend(request.POST.getlist('anturit'))
        startDate = datetime.strptime(request.POST.get('startDate'), "%Y-%m-%d")
        endDate = datetime.strptime(request.POST.get('endDate'), "%Y-%m-%d")
        vrk = request.POST.get('keskiarvo')=='vrk'
    else:
        fields.extend(['Sisalla','Ulkona'])

    df = objects_to_df(Temperature, fields, date__gte=startDate.timestamp()-UTC2, date__lte=endDate.timestamp()+24*60*60-UTC2)
    df['datetime'] = pd.to_datetime(df['date'], unit='s', utc=True)
    df = df.set_index('datetime').drop(columns=['date'])
    df = df.tz_convert(tz=timezone)
    if vrk:
        df = df.groupby(pd.Grouper(freq='D')).mean()
    save_figure(df,'line')
    return render(request, 'lampotilat/tempchart.html', 
        {'fields':field_names, 'prechecked': fields, 'sdate': startDate.strftime("%Y-%m-%d"), 'edate': endDate.strftime("%Y-%m-%d"), 'vrk': vrk})

def movchart(request):
    pass

def rainchart(request):
    pass