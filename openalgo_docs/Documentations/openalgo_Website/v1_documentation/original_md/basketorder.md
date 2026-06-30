# BasketOrder

## Endpoint URL

This API Function Place Basket Orders to the Broker

```http
Local Host   :  POST http://127.0.0.1:5000/api/v1/basketorder
Ngrok Domain :  POST https://<your-ngrok-domain>.ngrok-free.app/api/v1/basketorder
Custom Domain:  POST https://<your-custom-domain>/api/v1/basketorder
```

## Sample API Request

```json
{
    "apikey": "<your_app_apikey>",
    "strategy": "your-strategy",
    "orders": [
        {
            "symbol": "RELIANCE",
            "exchange": "NSE",
            "action": "BUY",
            "quantity": "1",
            "pricetype": "MARKET",
            "product": "MIS"
        },
        {
            "symbol": "INFY",
            "exchange": "NSE",
            "action": "SELL",
            "quantity": "1",
            "pricetype": "MARKET",
            "product": "MIS"
        }
    ]
}

```

###

## Sample API Response

```json
{
  "results": [
    {
      "orderid": "24120900343250",
      "status": "success",
      "symbol": "INFY"
    },
    {
      "orderid": "24120900343249",
      "status": "success",
      "symbol": "RELIANCE"
    }
  ],
  "status": "success"
}
```

###

## Parameter Description

| Parameters          | Description        | Mandatory/Optional | Default Value |
| ------------------- | ------------------ | ------------------ | ------------- |
| apikey              | App API key        | Mandatory          | -             |
| strategy            | Strategy name      | Mandatory          | -             |
| exchange            | Exchange code      | Mandatory          | -             |
| symbol              | Trading symbol     | Mandatory          | -             |
| action              | Action (BUY/SELL)  | Mandatory          | -             |
| product             | Product type       | Optional           | MIS           |
| pricetype           | Price type         | Optional           | MARKET        |
| quantity            | Quantity           | Mandatory          | -             |
| price               | Price              | Optional           | 0             |
| trigger\_price      | Trigger price      | Optional           | 0             |
| disclosed\_quantity | Disclosed quantity | Optional           | 0             |
