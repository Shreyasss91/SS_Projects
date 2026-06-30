# ModifyGttOrder

### ~~**Endpoint URL**~~

~~This API Function modifies an active GTT trigger. The body is a **full replacement** of the trigger spec — same shape as placegttorder plus trigger\_id. Send every field you want to keep — modify is not a patch.~~

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

### ~~**Sample API Request**~~

~~**SINGLE — move the IDEA dip-buy from 9.55 → 9.65, raise the limit to 9.60**~~

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

~~**OCO — tighten the INFY bracket: stop 1480 → 1485, target 1620 → 1625**~~

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

### ~~**Sample API Response**~~

```json
{
    "status": "success",
    "trigger_id": "23132604291205"
}
```

| Parameters       | Description                                                                                                         | Mandatory/Optional | Default Valueapikey |
| ---------------- | ------------------------------------------------------------------------------------------------------------------- | ------------------ | ------------------- |
| apikey           | App API key                                                                                                         | Mandatory          | -                   |
| strategy         | Strategy name                                                                                                       | Mandatory          | -                   |
| trigger\_id      | The trigger ID returned by placegttorder — identifies which active GTT to modify                                    | Mandatory          | -                   |
| trigger\_type    | SINGLE  or OCO - must match the original trigger's type (cannot switch)                                             | Mandatory          | -                   |
| exchange         | Exchange code (NSE, BSE, NFO, BFO, CDS, BCD, MCX)                                                                   | Mandatory          | -                   |
| symbol           | Trading symbol in OpenAlgo format                                                                                   | Mandatory          | -                   |
| action           | BUY or SELL .For OCO, applies to both legs.                                                                         | Mandatory          | -                   |
| product          | CNC (equity delivery) or NRML (F\&O overnight). MIS is not supported — GTTs can sit for days.                       | Mandatory          | -                   |
| quantity         | New order quantity                                                                                                  | Mandatory          | -                   |
| pricetype        | LIMIT or MARKET                                                                                                     | Optional           | LIMIT               |
| price            | SINGLE-only limit price for the child order. Send 0 when pricetype=MARKET. Ignored for OCO.                         | Mandatory          | -                   |
| triggerprice\_sl | New trigger price below LTP. **SINGLE**: use this or triggerprice\_tg. **OCO**: required (the stoploss-leg trigger) | Conditional        | 0                   |
| triggerprice\_tg | New trigger price above LTP. **SINGLE**: use this OR triggerprice\_tg. **OCO**: required (the target-leg trigger).  | Conditional        | 0                   |
| stoploss         | OCO-only new limit price for the stoploss leg's child order. Ignored for SINGLE.                                    | Conditional        | 0                   |
| target           | OCO-only new limit price for the target leg's child order. Ignored for SINGLE.                                      | Conditional        | 0                   |
