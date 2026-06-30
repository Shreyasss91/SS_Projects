# Placeorder

## Endpoint URL

This API Function Place Orders to the Broker

```http
Local Host   :  POST http://127.0.0.1:5000/api/v1/placeorder
Ngrok Domain :  POST https://<your-ngrok-domain>.ngrok-free.app/api/v1/placeorder
Custom Domain:  POST https://<your-custom-domain>/api/v1/placeorder
```

```json
{
    "apikey": "<your_app_apikey>",
    "strategy": "Test Strategy", 
    "symbol":"SAIL", 
    "action":"BUY", 
    "exchange":"NSE", 
    "pricetype":"MARKET", 
    "product":"MIS", 
    "quantity":"1" 
    
}

```

## Sample API Request

```json
{
    "apikey": "your_app_apikey",
    "strategy": "Test Strategy",
    "exchange": "NSE",
    "symbol": "BHEL",
    "action": "BUY",
    "product": "MIS",
    "pricetype": "MARKET",
    "quantity": "1",
    "price": "0",
    "trigger_price": "0",
    "disclosed_quantity": "0"
}
```

###

## Sample API Response

```json
{
    "orderid": "240307000614705",
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
