from django.http import HttpResponse
from django.shortcuts import render, redirect
from .models import Measurement
from django.db.models import Max

import numpy as np
import pandas as pd
import matplotlib 
import matplotlib.pyplot as plt
from datetime import datetime
import dateutil.relativedelta

timezone = 'Europe/Helsinki'
data_folder = 'lampotilat/data/'
chart_file = 'lampotilat/static/chart.png'
field_names = ['sisalla', 'ulkona', 'jarvessa', 'kellarissa', 'rauhalassa', 'saunassa']

def load_data(name, last_measurement):
    df = pd.read_csv(data_folder + name+'.csv', sep=',', warn_bad_lines=False, error_bad_lines=False, dtype=str)
    df.columns = ['epoch', 'data']
    df = df[df['epoch'].astype(int)>last_measurement*1000]
    df['date'] = pd.to_datetime(df['epoch'], unit='ms', utc=True)
    df[name] = pd.to_numeric(df['data'], errors='coerce')
    df = df.set_index('date').drop(columns=['epoch', 'data'])
    df = df.tz_convert(tz=timezone)
    df = df[df[name]<50]
    df = df[df[name]>-50]
    return df

def load_dataset(last_measurement):
    fields=[]
    for field in field_names:
        fields.append(load_data(field, last_measurement))
    df = pd.concat(fields)
    df = df.sort_values('date')
    df = df.groupby(pd.Grouper(freq='H')).mean()

    print(df)

    records = df.to_records()  # convert to records
    for record in records:
        measurement = Measurement(
            date = record[0].astype('datetime64[s]').astype('int'),
            sisalla = record[1], 
            ulkona = record[2], 
            jarvessa = record[3], 
            kellarissa = record[5],
            rauhalassa = record[4], 
            saunassa = record[6], 
        )
        measurement.save()

def setup(request):
    # Poistetaana viimeinen koska se on todennäköisesti puutteellinen
    epoch = last_measurement_epoch()
    if epoch!=None:
        Measurement.objects.filter(date=epoch).delete()
    load_dataset(last_measurement_epoch())


#    df_daily = df.groupby(pd.Grouper(freq='D')).mean()
    return redirect('/')

def last_measurement_epoch():
    return Measurement.objects.aggregate(Max('date'))['date__max']+60*60*2

def index(request):
    last_measurement = 'ei dataa'
    epoch = last_measurement_epoch()
    if epoch!=None:
        last_measurement = datetime.fromtimestamp(last_measurement_epoch()).strftime("%d.%m.%Y, %H:%M")
    return render(request, 'lampotilat/index.html', {'loaded': last_measurement})

def objects_to_df(model, fields, **kwargs):
    """
    Return a pandas dataframe containing the records in a model
    ``fields`` is an optional list of field names. If provided, return only the
    named.
    ``exclude`` is an optional list of field names. If provided, exclude the
    named from the returned dict, even if they are listed in the ``fields``
    argument.
    ``date_cols`` chart.js doesn't currently handle dates very well so these
    columns need to be converted to a string. Pass in the strftime string 
    that would work best as the first value followed by the column names.
    ex:  ['%Y-%m', 'dat_col1', 'date_col2']
    ``kwargs`` can be include to limit the model query to specific records
    """
    
    fields_wd=fields+['date']
    records = model.objects.filter(**kwargs).values_list(*fields_wd)
    df = pd.DataFrame(list(records), columns=fields_wd)

    return df

def charts(request):
    fields=[]
    now=datetime.now()
    endDate=now.strftime("%Y-%m-%d")
    date=now-dateutil.relativedelta.relativedelta(months=1)
    startDate=date.strftime("%Y-%m-%d")

    if request.method=="POST":
        fields.extend(request.POST.getlist('anturit'))
        startDate=request.POST.get('startDate')
        print(request.POST.values)
        endDate=request.POST.get('endDate')
    else:
        fields.extend(['sisalla','ulkona'])

    df = objects_to_df(Measurement, fields=fields)
    df['datetime'] = pd.to_datetime(df['date'], unit='s', utc=True)
    df = df.set_index('datetime').drop(columns=['date'])
    df = df.tz_convert(tz=timezone)

    df2 = df[fields].loc[startDate:endDate]
    plt.rcParams['figure.figsize'] = [12, 5]
    df2.plot()
    plt.legend(loc='best')
    plt.savefig(chart_file)
    return render(request, 'lampotilat/charts.html', 
        {'fields':field_names, 'prechecked': fields, 'sdate': startDate, 'edate': endDate})

