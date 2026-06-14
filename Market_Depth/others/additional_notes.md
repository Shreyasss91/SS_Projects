The market hours guard (is_market_hours) gates whether the monitor runs at all. 
The trading window guard gates whether orders are placed. 
These are separate concerns: you want data collection market hours (from 09:15 to 15:30), but trading only during specific windows (e.g., 09:30–11:30 and 13:30–15:00).
The  trading window guard belongs in strategy_bot.py inside on_alert, not in setup_engine.py (which is exchange-unaware) and not in the monitor (which controls data collection).

