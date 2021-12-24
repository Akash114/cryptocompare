import json

from django.http import HttpResponse
from django.shortcuts import render
from bitbnspy import bitbns
import pandas as pd
import requests
from functools import reduce
import warnings

warnings.filterwarnings('ignore')


# Create your views here.


def home(request):
    exchanges = merge_data()
    return render(request, 'index.html', {'exchanges': exchanges})


def merge_data():
    dfs = [get_bitbns(), get_wazirx(), get_coindcx(), get_zebpy()]
    df_final = reduce(lambda left, right: pd.merge(left, right, on='coin_name'), dfs)
    df_final[['coindcx_Price', 'wazirx_Price', 'bitbns_Price', 'zebpay_Price']] = df_final[
        ['coindcx_Price', 'wazirx_Price', 'bitbns_Price', 'zebpay_Price']].apply(pd.to_numeric)
    cols_of_interest = ['coindcx_Price', 'wazirx_Price', 'bitbns_Price', 'zebpay_Price']
    df_final['Change'] = df_final[cols_of_interest].max(axis=1) - df_final[cols_of_interest].min(axis=1)
    df_final['percentage_change'] = (df_final['Change'] / df_final[cols_of_interest].min(axis=1)) * 100
    df_final.reset_index(inplace=True)
    exchanges = df_final.to_dict('records')
    return exchanges


def data_table(request):
    exchanges = merge_data()
    return render(request, 'data.html', {'exchanges': exchanges})


def get_bitbns():
    bitbnsObj = bitbns.publicEndpoints()
    bitbns_data = bitbnsObj.fetchTickers()
    df_bitbns = pd.DataFrame(bitbns_data['data'])
    df_bitbns = df_bitbns.T
    df_bitbns.reset_index(inplace=True)
    df_bitbns_final = df_bitbns[['index', 'last_traded_price']]
    df_bitbns_final.rename(columns={'index': 'coin_name', 'last_traded_price': 'bitbns_Price'}, inplace=True)
    return df_bitbns_final


def get_coindcx():
    url = "https://api.coindcx.com/exchange/ticker"

    response = requests.get(url)
    data = response.json()
    df_coindcx = pd.DataFrame(data)
    df_coindcx_final = df_coindcx[df_coindcx['market'].str.endswith('INR')]
    df_coindcx_final['market'] = df_coindcx_final['market'].str[:-3]
    df_coindcx_final = df_coindcx_final[['market', 'last_price']]
    df_coindcx_final.rename(columns={'market': 'coin_name', 'last_price': 'coindcx_Price'}, inplace=True)
    return df_coindcx_final


def get_wazirx():
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'}

    url = "https://api.wazirx.com/sapi/v1/tickers/24hr"

    headers = {'Accept': 'application/json'}
    response = requests.get(url, headers=headers)
    data = response.json()
    df_wazirx = pd.DataFrame(data)
    df_wazirx_final = df_wazirx[df_wazirx['quoteAsset'] == 'inr']
    df_wazirx_final['baseAsset'] = df_wazirx_final['baseAsset'].str.upper()
    df_wazirx_final = df_wazirx_final[['baseAsset', 'lastPrice']]
    df_wazirx_final.rename(columns={'baseAsset': 'coin_name', 'lastPrice': 'wazirx_Price'}, inplace=True)
    return df_wazirx_final


def get_zebpy():
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'}

    url = "https://www.zebapi.com/pro/v1/market/"

    headers = {'Accept': 'application/json'}
    # auth = HTTPBasicAuth('x-api-key', 'cRbHFJTlL6aSfZ0K2q7nj6MgV5Ih4hbA2fUG0ueO')

    response = requests.get(url, headers=headers)
    data = response.json()
    df_zebpay = pd.DataFrame(data)
    df_zebpay_final = df_zebpay[df_zebpay['currency'] == 'INR']
    df_zebpay_final = df_zebpay_final[['virtualCurrency', 'market']]
    df_zebpay_final.rename(columns={'virtualCurrency': 'coin_name', 'market': 'zebpay_Price'}, inplace=True)
    return df_zebpay_final


def get_all(request):
    try:
        exchanges = merge_data()
        return HttpResponse(json.dumps(exchanges), content_type='application/json')
    except:
        return HttpResponse(status=400)


def get_data(request):
    exchanges = request.GET.get('exchanges')
    try:
        required = exchanges.split(',')
        dfs = []
        dct = {'bitbns': get_bitbns(), 'wazirx': get_wazirx(), 'coindcx': get_coindcx(), 'zebpay': get_zebpy()}
        cols_of_interest = []

        for i in required:
            dfs.append(dct[i])
            cols_of_interest.append(i + '_Price')

        df_final = reduce(lambda left, right: pd.merge(left, right, on='coin_name'), dfs)
        df_final[cols_of_interest] = df_final[cols_of_interest].apply(pd.to_numeric)

        df_final['Change'] = df_final[cols_of_interest].max(axis=1) - df_final[cols_of_interest].min(axis=1)
        df_final['percentage_change'] = df_final['Change'] / df_final[cols_of_interest].min(axis=1)
        df_final.reset_index(inplace=True)
        output = df_final.to_dict('records')
        return HttpResponse(json.dumps(output), content_type='application/json')
    except:
        return HttpResponse(status=400)
