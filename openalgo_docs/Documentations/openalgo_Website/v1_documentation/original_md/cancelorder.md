# CancelOrder

## Endpoint URL

```http
Local Host   :  POST http://127.0.0.1:5000/api/v1/cancelorder
Ngrok Domain :  POST https://<your-ngrok-domain>.ngrok-free.app/api/v1/cancelorder
Custom Domain:  POST https://<your-custom-domain>/api/v1/cancelorder
```

## Sample API Request

```json

{
    "apikey": "<your_app_apikey>",
    "strategy": "Test Strategy",
    "orderid": "1000000123665912"
}
```

## Sample API Response

```json

{
        "orderid": "1000000123665912",
        "status": "success"
}

```

###

## Parameters Description

| Parameters | Description   | Mandatory/Optional | Default Value |
| ---------- | ------------- | ------------------ | ------------- |
| apikey     | App API key   | Mandatory          | -             |
| strategy   | Strategy name | Mandatory          | -             |
| orderid    | Order Id      | Mandatory          | -             |
