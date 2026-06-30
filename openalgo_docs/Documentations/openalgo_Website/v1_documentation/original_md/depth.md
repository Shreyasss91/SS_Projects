# Depth

## Endpoint URL

This API Function get Market Depth from the Broker

```http
Local Host   :  POST http://127.0.0.1:5000/api/v1/depth
Ngrok Domain :  POST https://<your-ngrok-domain>.ngrok-free.app/api/v1/depth
Custom Domain:  POST https://<your-custom-domain>/api/v1/depth
```

## Sample API Request

```json
{
    "apikey": "<your_app_apikey>",
    "symbol": "NIFTY31JUL25FUT",
    "exchange": "NFO"
}

```

###

## Sample API Response

```json
{
  "data": {
    "asks": [
      {
        "price": 25741.1,
        "quantity": 3675
      },
      {
        "price": 25744.9,
        "quantity": 150
      },
      {
        "price": 25745,
        "quantity": 600
      },
      {
        "price": 25745.1,
        "quantity": 75
      },
      {
        "price": 25745.2,
        "quantity": 150
      }
    ],
    "bids": [
      {
        "price": 25741,
        "quantity": 150
      },
      {
        "price": 25740,
        "quantity": 375
      },
      {
        "price": 25739.9,
        "quantity": 600
      },
      {
        "price": 25739.8,
        "quantity": 150
      },
      {
        "price": 25739.7,
        "quantity": 75
      }
    ],
    "high": 25772.3,
    "low": 25635,
    "ltp": 25741.1,
    "ltq": 1050,
    "oi": 15056100,
    "open": 25695,
    "prev_close": 25615,
    "totalbuyqty": 789825,
    "totalsellqty": 386175,
    "volume": 3561150
  },
  "status": "success"
}
```

## Request Body

| Parameters | Description    | Mandatory/Optional | Default Value |
| ---------- | -------------- | ------------------ | ------------- |
| apikey     | App API key    | Mandatory          | -             |
| symbol     | Trading symbol | Mandatory          | -             |
| exchange   | Exchange code  | Mandatory          | -             |

## Response Fields

| Field        | Type   | Description                  |
| ------------ | ------ | ---------------------------- |
| asks         | array  | List of 5 best ask prices    |
| bids         | array  | List of 5 best bid prices    |
| totalbuyqty  | number | Total buy quantity           |
| totalsellqty | number | Total sell quantity          |
| high         | number | Day's high price             |
| low          | number | Day's low price              |
| ltp          | number | Last traded price            |
| ltq          | number | Last traded quantity         |
| open         | number | Opening price                |
| prev\_close  | number | Previous day's closing price |
| volume       | number | Total traded volume          |
| oi           | number | Open interest                |
