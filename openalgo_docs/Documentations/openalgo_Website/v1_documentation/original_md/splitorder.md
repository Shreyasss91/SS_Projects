# SplitOrder

## Endpoint URL

This API Function Place Split Orders to the Broker

```http
Local Host   :  POST http://127.0.0.1:5000/api/v1/splitorder
Ngrok Domain :  POST https://<your-ngrok-domain>.ngrok-free.app/api/v1/splitorder
Custom Domain:  POST https://<your-custom-domain>/api/v1/splitorder
```

## Sample API Request

```json
{
    "apikey": "<your_app_apikey>",
    "strategy": "Test Strategy",
    "exchange": "NSE",
    "symbol": "YESBANK",
    "action": "SELL",
    "quantity": "105",
    "splitsize": "20",
    "pricetype": "MARKET",
    "product": "MIS"
}
```

###

## Sample API Response

```json
{
  "results": [
    {
      "order_num": 1,
      "orderid": "24120900343417",
      "quantity": 20,
      "status": "success"
    },
    {
      "order_num": 2,
      "orderid": "24120900343419",
      "quantity": 20,
      "status": "success"
    },
    {
      "order_num": 3,
      "orderid": "24120900343420",
      "quantity": 20,
      "status": "success"
    },
    {
      "order_num": 4,
      "orderid": "24120900343418",
      "quantity": 20,
      "status": "success"
    },
    {
      "order_num": 5,
      "orderid": "24120900343421",
      "quantity": 20,
      "status": "success"
    },
    {
      "order_num": 6,
      "orderid": "24120900343416",
      "quantity": 5,
      "status": "success"
    }
  ],
  "split_size": 20,
  "status": "success",
  "total_quantity": 105
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
