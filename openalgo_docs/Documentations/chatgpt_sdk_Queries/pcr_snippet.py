
# ============================================================
# GET SPOT PRICE
# ============================================================

def get_spot_price():
    """
    Fetch NIFTY spot for ATM strike selection.
    """

    try:

        quote = client.quotes(
            symbol="NIFTY",
            exchange="NSE_INDEX"
        )

        ltp = quote["data"]["ltp"]

        return float(ltp)

    except Exception as e:

        print("Spot fetch error:", e)

        return 25000


# ============================================================
# BUILD OPTION CHAIN
# ============================================================

def build_option_symbols():

    spot = get_spot_price()

    atm = round(spot / STRIKE_STEP) * STRIKE_STEP

    symbols = []

    for i in range(-STRIKE_RANGE, STRIKE_RANGE + 1):

        strike = atm + i * STRIKE_STEP

        ce = f"{UNDERLYING}{EXPIRY}{strike}CE"
        pe = f"{UNDERLYING}{EXPIRY}{strike}PE"

        symbols.append({
            "exchange": "NFO",
            "symbol": ce
        })

        symbols.append({
            "exchange": "NFO",
            "symbol": pe
        })

    return symbols


# ============================================================
# PCR
# ============================================================

def calculate_pcr():

    total_ce = sum(ce_oi.values())
    total_pe = sum(pe_oi.values())

    if total_ce <= 0:
        return 0

    return round(total_pe / total_ce, 4)


# ============================================================
# QUOTE CALLBACK
# ============================================================

def on_quote(data):

    try:

        symbol = data.get("symbol")

        payload = data.get("data", {})

        # Broker-dependent field
        oi = payload.get("oi")

        if oi is None:
            return

        with lock:

            if symbol.endswith("CE"):
                ce_oi[symbol] = oi

            elif symbol.endswith("PE"):
                pe_oi[symbol] = oi

    except Exception as e:

        print("Quote callback error:", e)


# ============================================================
# CALCULATION LOOP
# ============================================================

def analytics_loop():

    while True:

        try:

            with lock:

                pcr = calculate_pcr()

                timestamps.append(datetime.now())

                pcr_series.append(pcr)

            print(
                f"{datetime.now().strftime('%H:%M:%S')} "
                f"PCR={pcr} "
            )

            time.sleep(1)

        except Exception as e:

            print("Analytics error:", e)



# ============================================================
# MAIN
# ============================================================

def main():

    symbols = build_option_symbols()

    print(f"Subscribing to {len(symbols)} contracts")

    client.connect()

    # Quote feed for OI
    client.subscribe_quote(
        symbols,
        on_data_received=on_quote
    )


    analytics_thread = threading.Thread(
        target=analytics_loop,
        daemon=True
    )

    dashboard_thread = threading.Thread(
        target=dashboard_loop,
        daemon=True
    )

    analytics_thread.start()
    dashboard_thread.start()

    try:

        while True:
            time.sleep(1)

    except KeyboardInterrupt:

        print("Stopping...")

        client.unsubscribe_quote(symbols)

        client.disconnect()


if __name__ == "__main__":
    main()