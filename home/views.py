from django.http import response
from django.db.models import Q
from django.http.response import JsonResponse
from django.views.generic import ListView, CreateView, DeleteView, UpdateView
from django.urls.base import reverse_lazy
from django.shortcuts import render, redirect
from django.conf import settings
from home.models import Asset, Portfolio
from home.forms import AssetForm, PortfolioForm

import requests
from pandas.io.json import json_normalize
from yahoo_fin import options
import plotly.express as px
import plotly
import plotly.graph_objs as go
import pandas as pd 

# Create your views here.

class MainView(ListView):
    model = Asset
    template_name = "home/asset_list.html"
    success_url = reverse_lazy('home:all')


    #def get_context_data(self,**kwargs):
    def get(self, request) :
        context = {}
        
        # Get Investment Accounts
        invest_accounts = Portfolio.objects.filter(type="investment")
        if not invest_accounts:
            portfolio = Portfolio(name="Default", cash=0.00)
            portfolio.save()
            invest_accounts = [portfolio]
        
        # Get Saving Accounts
        saving_accounts = Portfolio.objects.filter(type="saving")
        
        df = pd.DataFrame.from_records(Portfolio.objects.all().values())
        #print(df.head())
        
        # Track Investment Running Totals
        investment_list = []
        invest_total_book = 0
        invest_total_market = 0
        invest_total_cash = 0

        # Track Savings Running Totals
        saving_list = []
        total_cash = 0

        # Work in Progress...
        df = pd.DataFrame({'mass': [0.330, 4.87 , 5.97],
                   'radius': [2439.7, 6051.8, 6378.1]},
                  index=['Mercury', 'Venus', 'Earth'])
        trace1 = go.Pie(
                labels = df.index,
                values= df["mass"],
                name='OperatorShare'
                )
        data = [trace1]
        layout = go.Layout(
                        title='Test',
                        )
        fig = go.Figure(data=data, layout=layout)

        plot_div = plotly.offline.plot(fig, output_type='div')

        # Saving Account
        for account in saving_accounts:
            saving_list.append(account)
            total_cash += account.cash
            account.cash = "{:,}".format(round(account.cash,2))

        # Investment Account
        for account in invest_accounts:
            asset_set = account.asset_set.all()
            
            # Summary of Single Investment Account
            account_book = sum(float(asset.bookval) for asset in asset_set)
            account_market = sum(float(asset.marketval) for asset in asset_set)
            account_cash = float(account.cash)
            market, book, cash, c_yield, p_yield = get_summary(account_market, account_book, account_cash)
            account.marketval = market
            account.bookval = book
            account.cash = cash
            account.c_yield = c_yield
            account.p_yield = p_yield
            investment_list.append( {"account":account, "assets":asset_set}  )
            
            
            invest_total_book += account_book
            invest_total_cash += account_cash
            invest_total_market += account_market
            
        # Saving and Investment Details 
        context["savings_list"] = saving_list
        context["investment_list"] = investment_list

        # Summary of Total Investment Accounts 
        market, book, cash, c_yield, p_yield = get_summary(invest_total_market, invest_total_book, invest_total_cash)
        context["invest_total"] = {"market":market, "book":book, "p_yield":p_yield, "c_yield":c_yield, "cash":cash}

        # Summary of Total Net Worth
        total_cash = float(total_cash) + invest_total_cash - invest_total_book
        total_net = total_cash + invest_total_market
        total_cash = "{:,}".format(round(total_cash,2))
        total_net = "{:,}".format(round(total_net,2))
        context["net_total"] = {"cash":total_cash, "assets":market, "net":total_net}

        return render(request, self.template_name, context)
    
    def post(self, request):
        get_asset_list()
        return redirect(self.success_url)




def get_summary(in_market, in_book, in_cash):
    market = "{:,}".format(round(in_market,2))
    book = "{:,}".format(round(in_book,2))
    cash = "{:,}".format(round(in_cash - in_book,2))

    c_yield= "{:,}".format(round((in_market - in_book), 2))
    if in_book > 0:
        p_yield= round((in_market/in_book - 1) * 100, 2)
    else: 
        p_yield = 0  
    
    return market, book, cash, c_yield, p_yield

def get_crypto_list(crypto_list):
    url = "https://coingecko.p.rapidapi.com/simple/price"
    ids = ",".join(crypto_list)
    querystring = {"ids":ids,"vs_currencies":"usd"}
    headers = settings.API_KEYS["coingecko"]
    try:
        response = requests.get(url, headers=headers, params=querystring)
        data = response.json()
        data = {key:val["usd"] for key, val in data.items()}

    except requests.exceptions.HTTPError as e:
        print (e.response.text)
        data =  None

    return data


def get_asset_list():
    portfolios = Portfolio.objects.all() 

    for portfolio in portfolios:
            
        crypto_equity_set = portfolio.asset_set.filter(Q(type="crypto") | Q(type="equity"))
        option_set = portfolio.asset_set.filter(type="option")
        url = "https://alpha-vantage.p.rapidapi.com/query"
    
        for asset in crypto_equity_set:
            try:
                querystring = {"function":"GLOBAL_QUOTE","symbol":asset.name}
                headers = settings.API_KEYS["alpha-vantage"]
                response = requests.request("GET", url, headers=headers, params=querystring)
                data = response.json() 
                price = round(float(data["Global Quote"]['05. price']),2)
                print("Asset:{}  Price:{}".format(asset.name, price))
                asset.current_price = price
                asset = get_asset_summary(asset)
                asset.save()
            except requests.exceptions.HTTPError as e:
                print("Failed to update ASSET Price for {}".format(asset.name) )
                print (e.response.text)
        
        for asset in option_set:
            try:
                ticker = asset.name
                expiry_date = asset.option_expiry.strftime('%m/%d/%y')
                chain = options.get_options_chain(ticker, expiry_date)
                option_type = asset.option_type
                price = chain[option_type][chain[option_type]['Strike'] == asset.option_strike]["Last Price"]
                print("Asset:{} Option Price:{}".format(ticker, price))
                asset.current_price = round(price.item(),2)
                asset = get_asset_summary(asset)
                asset.save()
            except requests.exceptions.HTTPError as e:
                print("Failed to update OPTION Price for {}".format(asset.name) )
                print (e.response.text)


def get_asset_summary(asset):
    adj = 1
    if (asset.type == "option"):
        adj = 100

    current_price  = float(asset.current_price)
    size = float(asset.size)
    entry_price = float(asset.entry_price)
    book_value = round(entry_price * (size*adj),2)
    market_value = round(current_price * (size*adj),2)
    
    asset.profit = round(market_value - book_value,2)
    asset.marketval = market_value
    asset.bookval = book_value

    return asset

class AssetCreate(CreateView):
    model = Asset
    form_class = AssetForm
    success_url = reverse_lazy('home:all')


class AssetUpdate(UpdateView):
    model = Asset
    form_class = AssetForm
    success_url = reverse_lazy('home:all')

class AssetDelete(DeleteView):
    model = Asset
    fields = '__all__'
    success_url = reverse_lazy('home:all')

class PortfolioCreate(CreateView):
    model = Portfolio
    form_class = PortfolioForm
    success_url = reverse_lazy('home:all')

class PortfolioUpdate(UpdateView):
    model = Portfolio
    form_class = PortfolioForm
    success_url = reverse_lazy('home:all')

class PortfolioDelete(DeleteView):
    model = Portfolio
    fields = '__all__'
    success_url = reverse_lazy('home:all')

# Archived Function
def autocomplete(request):
    
    url = "https://coingecko.p.rapidapi.com/exchanges/gdax/tickers"
    headers = settings.API_KEYS["coingecko"]
    param = request.GET.get('term', None)

    try:
        response = requests.request("GET", url, headers=headers)
        data = response.json()
        coin_ids = json_normalize(data["tickers"], sep="_")
        temp = coin_ids["coin_id"].tolist()
        filtered = set(filter(lambda coin : coin.startswith(param), temp))
        data = list(filtered)
        status = 200

    except requests.exceptions.HTTPError as e:
        print (e.response.text)
        data = None
        status = 500

    return  JsonResponse({'status': status, 'data': data})    