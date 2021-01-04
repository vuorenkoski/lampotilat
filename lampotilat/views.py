from django.http import HttpResponse
from django.shortcuts import render, redirect
from .models import Temperature
from django.db.models import Max

from .load_data import load_dataset
import numpy as np
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
from datetime import datetime
from dateutil import tz, relativedelta
import os

data_folder = '/var/www/html/nuottis/data/'
#data_folder = 'lampotilat/data/'
chart_file = 'lampotilat/static/lampotilat/chart.png'
path = '/home/pi/serveri/lampotilat_app/lampotilat/'
#path = ''
csv_files = ['sisalla', 'ulkona', 'jarvessa', 'kellarissa', 'rauhalassa', 'saunassa', 'lampo_roykka']
field_names = ['Sisalla', 'Ulkona', 'Jarvessa', 'Kellarissa', 'Rauhalassa', 'Saunassa', 'Roykassa']
timezone = 'Europe/Helsinki'
timez = tz.gettz(timezone)
os.environ['TZ'] = timezone

def save_figure(df, kind, unit):
    fig = df.plot(kind=kind,  figsize=(12, 5), fontsize=14).get_figure()
    fig.axes[0].legend(loc='best', fontsize=14)
    fig.axes[0].set_ylabel(unit, fontsize=14)
    fig.axes[0].set_xlabel('')
    fig.axes[0].grid(axis='y')
    fig.savefig(path+chart_file)

def setup(request):
    # Poistetaana viimeinen koska se on todennäköisesti puutteellinen
    epoch = last_measurement_epoch()
    if epoch>0:
        Temperature.objects.filter(date=epoch).delete()
    load_dataset(epoch, csv_files, data_folder)
    return redirect('/')

def last_measurement_epoch():
    max=Temperature.objects.aggregate(Max('date'))['date__max']
    if max==None:
        return 0
    return max

def index(request):
    last_measurement = 'ei dataa'
    epoch = last_measurement_epoch()
    if epoch>0:
        last_measurement = datetime.fromtimestamp(epoch, timez).strftime("%d.%m.%Y, %H:%M")
    return render(request, 'lampotilat/index.html', {'loaded': last_measurement})

def objects_to_df(model, fields, **kwargs):
    fields_wd=fields+['date']
    records = model.objects.filter(**kwargs).values_list(*fields_wd)
    df = pd.DataFrame(list(records), columns=fields_wd)
    df['datetime'] = pd.to_datetime(df['date'], unit='s', utc=True)
    df = df.set_index('datetime').drop(columns=['date'])
    df = df.tz_convert(tz=timezone)
    return df

def tempchart(request):
    fields = []
    endDate = datetime.now()
    startDate = endDate - relativedelta.relativedelta(months=1)
    vrk = False
    if request.method=="POST":
        fields.extend(request.POST.getlist('anturit'))
        startDate = datetime.strptime(request.POST.get('startDate'), "%Y-%m-%d")
        endDate = datetime.strptime(request.POST.get('endDate'), "%Y-%m-%d")
        vrk = request.POST.get('keskiarvo')=='vrk'
    else:
        fields.extend(['Sisalla','Ulkona'])

    df = objects_to_df(Temperature, fields, date__gte=startDate.timestamp(), date__lte=endDate.timestamp()+24*60*60)

    if vrk:
        df = df.groupby(pd.Grouper(freq='D')).mean()
    save_figure(df,'line','celsius')
    return render(request, 'lampotilat/tempchart.html', 
        {'fields':field_names, 'prechecked': fields, 'sdate': startDate.strftime("%Y-%m-%d"), 'edate': endDate.strftime("%Y-%m-%d"), 'vrk': vrk})

def movechart(request):
    endDate = datetime.now()
    startDate = endDate - relativedelta.relativedelta(months=1)
    vrk = True
    if request.method=="POST":
        startDate = datetime.strptime(request.POST.get('startDate'), "%Y-%m-%d")
        endDate = datetime.strptime(request.POST.get('endDate'), "%Y-%m-%d")
        vrk = request.POST.get('keskiarvo')=='vrk'
    df = objects_to_df(Temperature, ['Liike'], date__gte=startDate.timestamp(), date__lte=endDate.timestamp()+24*60*60)

    if vrk:
        df = df.groupby(pd.Grouper(freq='D')).sum()
    save_figure(df,'line','lukumaara')
    return render(request, 'lampotilat/movechart.html', 
        {'sdate': startDate.strftime("%Y-%m-%d"), 'edate': endDate.strftime("%Y-%m-%d"), 'vrk': vrk})

def rainchart(request):
    endDate = datetime.now()
    startDate = endDate - relativedelta.relativedelta(months=1)
    vrk = True
    if request.method=="POST":
        startDate = datetime.strptime(request.POST.get('startDate'), "%Y-%m-%d")
        endDate = datetime.strptime(request.POST.get('endDate'), "%Y-%m-%d")
        vrk = request.POST.get('keskiarvo')=='vrk'
    df = objects_to_df(Temperature, ['Sade', 'Lumi'], date__gte=startDate.timestamp(), date__lte=endDate.timestamp()+24*60*60)

    if vrk:
        df = df.groupby(pd.Grouper(freq='D')).agg({'Sade':'sum', 'Lumi':'mean'})
    save_figure(df,'line','mm')
    return render(request, 'lampotilat/rainchart.html', 
        {'sdate': startDate.strftime("%Y-%m-%d"), 'edate': endDate.strftime("%Y-%m-%d"), 'vrk': vrk})

def windchart(request):
    endDate = datetime.now()
    startDate = endDate - relativedelta.relativedelta(months=1)
    vrk = False
    if request.method=="POST":
        startDate = datetime.strptime(request.POST.get('startDate'), "%Y-%m-%d")
        endDate = datetime.strptime(request.POST.get('endDate'), "%Y-%m-%d")
        vrk = request.POST.get('keskiarvo')=='vrk'
    df = objects_to_df(Temperature, ['Tuuli', 'Tuulimax'], date__gte=startDate.timestamp(), date__lte=endDate.timestamp()+24*60*60)

    if vrk:
         df = df.groupby(pd.Grouper(freq='D')).agg({'Tuuli':'mean', 'Tuulimax':'max'})
    save_figure(df,'line','m/s')
    return render(request, 'lampotilat/windchart.html', 
        {'sdate': startDate.strftime("%Y-%m-%d"), 'edate': endDate.strftime("%Y-%m-%d"), 'vrk': vrk})

def means(request):
    year=2020
    if request.method=="POST":
        year = int(request.POST.get('year'))
    df = objects_to_df(Temperature, ['Sisalla', 'Ulkona', 'Jarvessa', 'Kellarissa'])
    df = df.groupby(pd.Grouper(freq='D')).mean()
    df['month'] = pd.DatetimeIndex(df.index).month
    df['year'] = pd.DatetimeIndex(df.index).year
    years = df.year.unique()
    df_monthly = df[df['year']==year].groupby(pd.Grouper(freq='M')).mean().set_index('month')
    df_diff = df_monthly-df.drop(columns=['year']).groupby(['month']).mean()
    df_years = df.groupby('year').mean()
    table1 = df_monthly.to_html(columns=['Sisalla', 'Ulkona', 'Jarvessa', 'Kellarissa'], 
        index=True, float_format='%.1f', na_rep='')
    table2 = df_monthly.mean().to_frame().T.to_html(columns=['Sisalla', 'Ulkona', 'Jarvessa', 'Kellarissa'], 
        index=False, float_format='%.1f', na_rep='')
    table3 = df_diff.to_html(columns=['Sisalla', 'Ulkona', 'Jarvessa', 'Kellarissa'], 
        index=True, float_format='%.1f', na_rep='')
    table4 = df_diff.mean().to_frame().T.to_html(columns=['Sisalla', 'Ulkona', 'Jarvessa', 'Kellarissa'], 
        index=False, float_format='%.1f', na_rep='')
    table5 = df_years.to_html(columns=['Sisalla', 'Ulkona', 'Jarvessa', 'Kellarissa'], 
        index=True, float_format='%.1f', na_rep='')

    return render(request, 'lampotilat/means.html', {'table1_code':table1, 
        'table2_code':table2, 'table3_code':table3, 'table4_code':table4, 
        'table5_code':table5, 'years': years, 'prechecked': year}) 
