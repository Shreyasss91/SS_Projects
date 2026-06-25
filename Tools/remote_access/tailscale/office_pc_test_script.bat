@echo off

echo ==========================
echo OpenAlgo Connectivity Test
echo ==========================

echo.
echo ---- Tailscale ----
tailscale status

echo.
echo ---- Listening Port ----
netstat -ano | findstr :5000

echo.
echo ---- Ping Mobile: Pinging 100.86.146.33----
ping 100.86.146.33

pause