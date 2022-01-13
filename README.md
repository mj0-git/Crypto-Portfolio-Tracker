# Portfolio Watch
I could never find an app that conveniently consolidates all displays of my financial portfolios.. so I created "Portfolio Watch" using Django and a few APIs to track equities, crypto, and option prices. 

![](./images/home.png)

Keep track of all your ongoing trades, including tracking entry, target, stop loss, and current price. Seamlessly integrated with yahoo_fin and alpha-vantage API, portfolio quotes can be updated with a single button click. 

![](./images/add.png)

My long-term vision of Portfolio Watch is to be a one-stop-shop for tracking your entire financial status - ongoing investments, current savings, loans, expenses, and more. Time being, I have included a test database for your use; please follow the instructions below to get started

## Setup 
1. Install requirements (Recommend to use virtual env)
    ``` 
    pip install -r requirements.txt
    ```
2. Create new migration
    ``` 
    python manage.py makemigrations
    ```
3. Apply migrations
    ``` 
    python manage.py migrate
    ```

4. Obtain Free API key for AlphaVantage from __[RapidAPI](https://rapidapi.com/hub)__, write to  __secrets-example.json__, and rename file to __secrets.json__ 
__Please Note__: You must complete this step in order to refresh quotes!
    ``` 
    mv  secrets-example.json secrets.json
    ```

Execute ```python manage.py runserver ``` and navigate  to `http://localhost:8000/`
