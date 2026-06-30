# CancelGttOrder

### **Endpoint URL**

This API Function cancels an active GTT trigger by its `trigger_id`. Cancelling an OCO removes both legs atomically.

```
Local Host   :  POST http://127.0.0.1:5000/api/v1/cancelgttorder
Ngrok Domain :  POST https://<your-ngrok-domain>.ngrok-free.app/api/v1/cancelgttorder
Custom Domain:  POST https://<your-custom-domain>/api/v1/cancelgttorder
```

```json
{
    "apikey": "<your_app_apikey>",
    "strategy": "My GTT Strategy",
    "trigger_id": "23132604291205"
}
```

### **Sample API Request**

```json
{
    "apikey": "<your_app_apikey>",
    "strategy": "My GTT Strategy",
    "trigger_id": "23132604291205"
}
```

### **Sample API Response**

```json
{
    "status": "success",
    "trigger_id": "23132604291205"
}
```

### **Endpoint URL**

This API Function modifies an active GTT trigger. The body is a **full replacement** of the trigger spec — same shape as placegttorder plus trigger\_id. Send every field you want to keep — modify is not a patch.

```json
Local Host   :  POST http://127.0.0.1:5000/api/v1/modifygttorder
Ngrok Domain :  POST https://<your-ngrok-domain>.ngrok-free.app/api/v1/modifygttorder
Custom Domain:  POST https://<your-custom-domain>/api/v1/modifygttorder
```

```json
{
    "apikey": "<your_app_apikey>",
    "strategy": "My GTT Strategy",
    "trigger_id": "23132604291205",
    "trigger_type": "SINGLE",
    "exchange": "NSE",
    "symbol": "IDEA",
    "action": "BUY",
    "product": "CNC",
    "quantity": 1,
    "pricetype": "LIMIT",
    "price": 9.60,
    "triggerprice_sl": 9.65,
    "triggerprice_tg": 0,
    "stoploss": null,
    "target": null
}
```

### **Sample API Request**

**SINGLE — move the IDEA dip-buy from 9.55 → 9.65, raise the limit to 9.60**

```json
{
    "apikey": "<your_app_apikey>",
    "strategy": "My GTT Strategy",
    "trigger_id": "23132604291205",
    "trigger_type": "SINGLE",
    "exchange": "NSE",
    "symbol": "IDEA",
    "action": "BUY",
    "product": "CNC",
    "quantity": 1,
    "pricetype": "LIMIT",
    "price": 9.60,
    "triggerprice_sl": 9.65,
    "triggerprice_tg": 0,
    "stoploss": null,
    "target": null
}
```

**OCO — tighten the INFY bracket: stop 1480 → 1485, target 1620 → 1625**

```json
{
    "apikey": "<your_app_apikey>",
    "strategy": "Bracket OCO",
    "trigger_id": "23132604291213",
    "trigger_type": "OCO",
    "exchange": "NSE",
    "symbol": "INFY",
    "action": "SELL",
    "product": "CNC",
    "quantity": 5,
    "pricetype": "LIMIT",
    "price": 0,
    "triggerprice_sl": 1485,
    "stoploss": 1483,
    "triggerprice_tg": 1625,
    "target": 1627
}
```

### **Sample API Response**

```json
{
    "status": "success",
    "trigger_id": "23132604291205"
}
```

| Parameters  | Description                                                            | Mandatory/Optional | Default Value |
| ----------- | ---------------------------------------------------------------------- | ------------------ | ------------- |
| apikey      | App API key                                                            | Mandatory          | -             |
| strategy    | Strategy name (used in event logs)                                     | Mandatory          | -             |
| trigger\_id | The trigger ID of the active GTT to cancel (returned by placegttorder) | Mandatory          | -             |
