# OpenPosition

## Endpoint URL

```
Local Host   :  POST http://127.0.0.1:5000/api/v1/openposition
Ngrok Domain :  POST https://<your-ngrok-domain>.ngrok-free.app/api/v1/openposition
Custom Domain:  POST https://<your-custom-domain>/api/v1/openposition
```

## Sample API Request

<pre class="language-json"><code class="lang-json">{
<strong>    "apikey":"&#x3C;your_app_apikey>",
</strong>    "strategy": "Test Strategy",
    "symbol": "YESBANK",
    "exchange": "NSE",
    "product": "CNC"
}
</code></pre>

## Sample API Response

```json
{
  "quantity": 10,
  "status": "success"
}
```

###

## Parameters Description

| Parameters | Description    | Mandatory/Optional | Default Value |
| ---------- | -------------- | ------------------ | ------------- |
| apikey     | App API key    | Mandatory          | -             |
| strategy   | Strategy name  | Mandatory          | -             |
| Symbol     | Trading Symbol | Mandatory          | -             |
| Exchange   | Exchange       | Mandatory          | -             |
| Product    | Product        | Mandatory          | -             |
