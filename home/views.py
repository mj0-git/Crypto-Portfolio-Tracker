from django.http.response import JsonResponse
from django.views.generic import ListView, CreateView, DeleteView, UpdateView
from django.urls.base import reverse_lazy
from django.conf import settings
from home.models import Asset
from home.forms import AssetForm

import requests
from pandas.io.json import json_normalize

# Create your views here.

class MainView(ListView):
    model = Asset
    template_name = "asset_list.html"

    def get_context_data(self,**kwargs):
       
        context = super().get_context_data(**kwargs)
        q_set = Asset.objects.all().filter(type="crypto")
        
        if(q_set):
            crypto_list = [q.name.lower() for q in q_set]
            result = get_crypto_list(crypto_list)
            if result:
                for q in q_set:
                    if q.name.lower() in result:
                        current_price = float(result[q.name.lower()])
                        size = float(q.size)
                        entry_price = float(q.entry_price)
                        q.current_price = current_price
                        q.profit = round((current_price * size) - (entry_price * size),2)
                context["asset_list"] = q_set

        return context


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
    

class AssetCreate(CreateView):
    model = Asset
    form_class = AssetForm
    success_url = reverse_lazy('home:all')


class AssetUpdate(UpdateView):
    model = Asset
    form_class = AssetForm
    success_url = reverse_lazy('home:all')


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

class AssetDelete(DeleteView):
    model = Asset
    fields = '__all__'
    success_url = reverse_lazy('home:all')
