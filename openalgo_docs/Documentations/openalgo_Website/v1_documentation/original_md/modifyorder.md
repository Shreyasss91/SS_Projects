# ModifyOrder

## Endpoint URL

```http
Local Host   :  POST http://127.0.0.1:5000/api/v1/modifyorder
Ngrok Domain :  POST https://<your-ngrok-domain>.ngrok-free.app/api/v1/modifyorder
Custom Domain:  POST https://<your-custom-domain>/api/v1/modifyorder
```

## Sample API Request

```json
{
    "apikey": "<your_app_apikey",
    "strategy": "Test Message",
    "symbol": "USDINR15MAR2483CE",
    "action": "BUY",
    "exchange": "CDS",
    "orderid":"240307000562466",
    "product":"NRML",
    "pricetype":"LIMIT",
    "price":"0.0050",
    "quantity":"1",
    "disclosed_quantity":"0",
    "trigger_price":"0"
}

```

## Sample API Response

```json
{
        "orderid": "240307000562466",
        "status": "success"
}

```

## Parameter Description

| Parameters          | Description        | Mandatory/Optional | Default Value |
| ------------------- | ------------------ | ------------------ | ------------- |
| apikey              | App API key        | Mandatory          | -             |
| strategy            | Strategy name      | Mandatory          | -             |
| symbol              | Trading Symbol     | Mandatory          | -             |
| action              | Action (BUY/SELL)  | Mandatory          | -             |
| exchange            | Exchange           | Mandatory          | -             |
| orderid             | Order ID           | Mandatory          | -             |
| product             | Product type       | Mandatory          | -             |
| pricetype           | Price type         | Mandatory          | -             |
| quantity            | Quantity           | Mandatory          | -             |
| price               | Price              | Mandatory          | 0             |
| trigger\_price      | Trigger price      | Mandatory          | 0             |
| disclosed\_quantity | Disclosed quantity | Mandatory          | 0             |
