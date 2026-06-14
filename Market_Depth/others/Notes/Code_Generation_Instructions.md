> Requirements:
>
> - Use NumPy for vectorized computation.
> - Use `collections.deque` for temporal state.
> - Use pre-allocated arrays for the `4X+1` strike universe.
> - Support configurable depth levels (`N=5` or `N=10`).
> - Implement all mathematical formulas exactly as specified.
> - Generate Small, Medium, and Large window aggregations.
> - Implement temporal velocity metrics and LMI.
> - Include anomaly detection, packet timeout handling, and Z-score normalization.
> - Expose a low-latency `on_tick()` API suitable for websocket market data feeds.
> - Optimize for sub-10ms processing latency.