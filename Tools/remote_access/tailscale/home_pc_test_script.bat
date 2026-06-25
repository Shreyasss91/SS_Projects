@echo off

echo ==========================
echo Remote Connectivity Test
echo ==========================

echo.

echo ---- Ping Office(check whether ip address is correct from -: tailscale status): pinging 100.108.179.50 ----
ping 100.108.179.50

echo.
echo If ping succeeds,
echo Open

echo.
echo http://100.108.179.50:5000

pause