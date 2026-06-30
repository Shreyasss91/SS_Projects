# PlaceSmartOrder

Place Order Smartly by analyzing the current open position. It matches the Position Size with the given position book. Buy/Sell Signal Orders will be traded accordingly to the Position Size

## Endpoint URL

```http
Local Host   :  POST http://127.0.0.1:5000/api/v1/placesmartorder
Ngrok Domain :  POST https://<your-ngrok-domain>.ngrok-free.app/api/v1/placesmartorder
Custom Domain:  POST https://<your-custom-domain>/api/v1/placesmartorder
```

## Sample API Request

```json
{
    "apikey": "<your_app_apikey>",
    "strategy": "Test Strategy",
    "exchange": "NSE",
    "symbol": "IDEA",
    "action": "BUY",
    "product": "MIS",
    "pricetype": "MARKET",
    "quantity": "1",
    "position_size": "5",
    "price": "0",
    "trigger_price": "0",
    "disclosed_quantity": "0"
}
```

## Sample API Response

```json
{
    "orderid": "240307000616990",
    "status": "success"
}
```

## Parameters Description

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
| position\_size      | Position Size      | Mandatory          | -             |
| price               | Price              | Optional           | 0             |
| trigger\_price      | Trigger price      | Optional           | 0             |
| disclosed\_quantity | Disclosed quantity | Optional           | 0             |

## How PlaceSmartOrder API Works?

{% embed url="<https://www.youtube.com/watch?v=bC46E1GV4gY>" %}

PlaceSmartOrder API function, which allows traders to build intelligent trading systems that can automatically place orders based on existing trade positions in the position book.

| Action | Qty (API) | Pos Size (API) | Current Open Pos | Action by OpenAlgo                      |
| ------ | --------- | -------------- | ---------------- | --------------------------------------- |
| BUY    | 100       | 0              | 0                | No Open Pos Found. Buy +100 qty         |
| BUY    | 100       | 100            | -100             | BUY 200 to match Open Pos in API Param  |
| BUY    | 100       | 100            | 100              | No Action. Position matched             |
| BUY    | 100       | 200            | 100              | BUY 100 to match Open Pos in API Param  |
| SELL   | 100       | 0              | 0                | No Open Pos Found. SELL 100 qty         |
| SELL   | 100       | -100           | +100             | SELL 200 to match Open Pos in API Param |
| SELL   | 100       | -100           | -100             | No Action. Position matched             |
| SELL   | 100       | -200           | -100             | SELL 100 to match Open Pos in API Param |

<br>
