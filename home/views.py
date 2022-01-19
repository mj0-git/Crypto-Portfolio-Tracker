from unicodedata import name
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
import pandas_datareader.data as web
from pandas.io.json import json_normalize
from yahoo_fin import options
import plotly.express as px
import plotly
import pandas as pd 
import datetime

# ALPHA VANTAGE API
api = settings.API_KEYS["alpha-vantage"]
url = api["host"]
key = api["key"]

class MainView(ListView):
    model = Asset
    template_name = "home/asset_list.html"
    success_url = reverse_lazy('home:all')


    #def get_context_data(self,**kwargs):
    def get(self, request) :
        context = {}
        
        # Get Accounts
        invest_accounts = Portfolio.objects.filter(type="investment")
        saving_accounts = Portfolio.objects.filter(type="saving")
        if not invest_accounts:
            portfolio = Portfolio(name="Default", cash=0.00)
            portfolio.save()
            invest_accounts = [portfolio]
        
        # Track Investment Running Totals
        investment_list = []
        invest_total_book = 0
        invest_total_market = 0
        invest_total_cash = 0

        # Track Savings Running Totals
        saving_list = []
        total_cash = 0
        saving_cash = 0

        # Saving Account
        for account in saving_accounts:
            saving_list.append(account)
            saving_cash += account.cash
            total_cash += account.cash
            account.cash = "{:,}".format(round(account.cash,2))

        # Investment Account
        df_total = pd.DataFrame()
        for account in invest_accounts:
            asset_set = account.asset_set.all()
            
            # Summary of Single Investment Account
            account_book = sum(float(asset.bookval) for asset in asset_set)
            account_market = sum(float(asset.marketval) for asset in asset_set)
            account_cash = float(account.cash)
            plot_div = None

            # Plot Account Balance History
            acct_series = account_balance_series(account)
            if not acct_series.empty:
                fig = plot_acct_balance(acct_series, acct_series.name)
                plot_div = plotly.offline.plot(fig, output_type='div')
                df_total = pd.concat([df_total, acct_series], axis=1 )
            

            investment_list.append( {"account":account, "assets":asset_set, "plot_div":plot_div}  )
            
            
            invest_total_book += account_book
            invest_total_cash += account_cash
            invest_total_market += account_market
        

        # Account & Asset Details 
        context["savings_list"] = saving_list
        context["investment_list"] = investment_list

        # Net Investment Accounts 
        total = round((invest_total_market + (invest_total_cash - invest_total_book) ), 2)
        context["invest_total"] = total

        # Total Net Worth
        total_cash = float(total_cash) + invest_total_cash - invest_total_book
        total_net = round(total_cash + invest_total_market,2)
        context["net_total"] = total_net

        # Plot Total Accounts Balance History
        df_total.fillna(method='ffill', inplace=True)
        col_names =list(df_total)
        df_total["total"] = df_total[col_names].sum(axis=1)
        df_total["total"] = df_total["total"] + float(saving_cash) # Add Saving Cash
        fig_total = plot_acct_balance(df_total, "total")
        fig_total['data'][0]['line']['color']='rgb(6, 23, 1)'
        fig_total['data'][0]['line']['width']=2
        plot_div_total = plotly.offline.plot(fig_total, output_type='div')
        context["plot_div_total"] = plot_div_total
        
        return render(request, self.template_name, context)
    
    def post(self, request):
        refresh_asset_quotes()
        refresh_portfolio_quotes()
        return redirect(self.success_url)


def plot_acct_balance(df, col):
    fig = px.line(df, x=df.index, y=col)
    fig.update_layout(title_text='')
    fig.update_xaxes(title_text='')
    fig.update_yaxes(title_text='')
    return fig  

def account_balance_series(account):
    
    # Dataframe to track historical Account Balance
    df = pd.DataFrame()

    # Get Options PNL - No price history available
    options = account.asset_set.filter(Q(type="option"))
    option_pnl = 0 
    if options:
         option_pnl = sum((float(option.current_price) - float(option.entry_price))*float(option.size)*100 for option in options)

    # Get Equity/Crypto to fetch historical price data 
    assets = account.asset_set.filter(Q(type="equity")| Q(type="crypto")).order_by('purchase_date')
    if assets:
        
        # Fix Crypto name for API Call      
        name_list = []
        for asset in assets: 
            if asset.type == "crypto":
                fix_name = asset.name.replace("USD","-USD")
                asset.name = fix_name
            name_list.append(asset.name)
        
        # Fetch istorical price data 
        # NOTE: Have to use yahoo given AlphaVantage api limit resitricitons
        df = web.DataReader(name_list, 'yahoo', start=assets[0].purchase_date, end=datetime.datetime.today().strftime('%Y-%m-%d'))
        df = df["Close"]

        # Add begining cash balance and track running
        df["acct_balance"] = float(account.cash)
        running_balance = float(account.cash) 

        # Calculate and store value of assets + cash per day
        for asset in assets:
            df.loc[:asset.purchase_date, asset.name] = 0
            size = df.loc[asset.purchase_date:, asset.name] * float(asset.size)
            df.loc[asset.purchase_date:, asset.name] = size
            running_balance = float(running_balance) - float(asset.bookval)
            df.loc[asset.purchase_date + datetime.timedelta(days=1):, "acct_balance"] =  running_balance
        
        # Forward fill NA with prev value (Occurs because of holidays given equity+crypto)
        df.fillna(method='ffill', inplace=True)
        
        # Calculate total account value (includes pnl)
        name = account.name + "_balance"
        col_names =list(df)
        df[name] = df[col_names].sum(axis=1)
        df[name] = df[name] + option_pnl

    return df[name]



def refresh_asset_quotes():
    portfolios = Portfolio.objects.all() 

    for portfolio in portfolios:
        crypto_equity_set = portfolio.asset_set.filter(Q(type="crypto") | Q(type="equity"))
        option_set = portfolio.asset_set.filter(type="option")
    
        for asset in crypto_equity_set:
            try:
                querystring = {"function":"GLOBAL_QUOTE","symbol":asset.name,"apikey":key}
                response = requests.request("GET", url, params=querystring)
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

def refresh_portfolio_quotes():
    
    portfolios = Portfolio.objects.filter(type="investment")
    for account in portfolios:
        asset_set = account.asset_set.all()
        account_book = sum(float(asset.bookval) for asset in asset_set)
        account_market = sum(float(asset.marketval) for asset in asset_set)
        begin_balance = float(account.cash)
        account_total = (account_market + (begin_balance - account_book))

        account.marketval = round(account_market,2)
        account.bookval =  round(account_book,2)
        account.net_cash = round(begin_balance - account_book,2)
        account.c_yield= round((account_market - account_book), 2)
        account.total = round(account_total, 2)

        
        if account_book > 0:
            account.p_yield= round((account_total/begin_balance -1) * 100, 2)
        else: 
            account.p_yield = 0 
        account.save()


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