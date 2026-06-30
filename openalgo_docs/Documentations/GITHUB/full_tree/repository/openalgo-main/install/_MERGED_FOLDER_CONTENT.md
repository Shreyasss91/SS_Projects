# Folder Merge

Folder: C:\Users\admin\Desktop\openalgo_docs\GITHUB\full_tree\repository\openalgo-main\install



---

# FILE: install\change-domain.sh

```sh
#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# OpenAlgo Domain Change Banner
echo -e "${BLUE}"
echo "  ██████╗ ██████╗ ███████╗███╗   ██╗ █████╗ ██╗      ██████╗  ██████╗ "
echo " ██╔═══██╗██╔══██╗██╔════╝████╗  ██║██╔══██╗██║     ██╔════╝ ██╔═══██╗"
echo " ██║   ██║██████╔╝███████╗██╔██╗ ██║███████║██║     ██║  ███╗██║   ██║"
echo " ██║   ██║██╔═══╝ ██╔══╝  ██║╚██╗██║██╔══██║██║     ██║   ██║██║   ██║"
echo " ╚██████╔╝██╗     ███████╗██║ ╚████║██║  ██║███████╗╚██████╔╝╚██████╔╝"
echo "  ╚═════╝ ╚═╝     ╚══════╝╚═╝  ╚═══╝╚═╝  ╚═╝╚══════╝ ╚═════╝  ╚═════╝ "
echo "                      DOMAIN  CHANGE  SCRIPT                             "
echo -e "${NC}"

# OpenAlgo Domain Change Script
# Changes the domain for an existing OpenAlgo server deployment.
# Updates .env, Nginx config, and obtains a new SSL certificate.

# Create logs directory if it doesn't exist
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
LOGS_DIR="$SCRIPT_DIR/logs"
mkdir -p "$LOGS_DIR"

# Generate unique log file name
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_FILE="$LOGS_DIR/change_domain_${TIMESTAMP}.log"

# Function to log messages to both console and log file
log_message() {
    local message="$1"
    local color="$2"
    echo -e "${color}${message}${NC}" | tee -a "$LOG_FILE"
}

# Function to check if command was successful
check_status() {
    if [ $? -ne 0 ]; then
        log_message "Error: $1" "$RED"
        exit 1
    fi
}

# Start logging
log_message "Starting OpenAlgo domain change log at: $LOG_FILE" "$BLUE"
log_message "----------------------------------------" "$BLUE"

# ============================================
# Step 1: Detect OS and set variables
# ============================================
OS_TYPE=$(grep -w "ID" /etc/os-release | cut -d "=" -f 2 | tr -d '"')

# Handle OS variants
case "$OS_TYPE" in
    "pop"|"linuxmint"|"zorin")
        OS_TYPE="ubuntu"
        ;;
    "manjaro"|"manjaro-arm"|"endeavouros"|"cachyos")
        OS_TYPE="arch"
        ;;
    "rocky"|"almalinux"|"ol")
        OS_TYPE="rhel"
        ;;
esac

# Set Nginx config paths based on OS
case "$OS_TYPE" in
    ubuntu|debian|raspbian)
        NGINX_AVAILABLE="/etc/nginx/sites-available"
        NGINX_ENABLED="/etc/nginx/sites-enabled"
        NGINX_CONFIG_MODE="sites"
        ;;
    centos|fedora|rhel|amzn|arch)
        NGINX_AVAILABLE="/etc/nginx/conf.d"
        NGINX_ENABLED="/etc/nginx/conf.d"
        NGINX_CONFIG_MODE="confd"
        ;;
    *)
        log_message "Warning: Unrecognized OS ($OS_TYPE). Defaulting to sites-available." "$YELLOW"
        NGINX_AVAILABLE="/etc/nginx/sites-available"
        NGINX_ENABLED="/etc/nginx/sites-enabled"
        NGINX_CONFIG_MODE="sites"
        ;;
esac

log_message "Detected OS: $OS_TYPE" "$GREEN"

# ============================================
# Step 2: Discover existing deployment
# ============================================
# Try the simple single-install layout (current install.sh) first, then
# fall back to scanning the legacy /var/python/openalgo-flask/ tree
# produced by older install.sh versions and install/install-multi.sh.
SIMPLE_PATH="/var/python/openalgo"
DEPLOY_BASE="/var/python/openalgo-flask"

if [ -f "$SIMPLE_PATH/.env" ]; then
    SELECTED_DEPLOY="openalgo"
    BASE_PATH="$SIMPLE_PATH"
    OPENALGO_PATH="$SIMPLE_PATH"
    SOCKET_FILE="$SIMPLE_PATH/openalgo.sock"
    SERVICE_NAME="openalgo"
    ENV_FILE="$OPENALGO_PATH/.env"
    log_message "Found OpenAlgo install at $SIMPLE_PATH" "$GREEN"
else
    if [ ! -d "$DEPLOY_BASE" ]; then
        log_message "Error: No OpenAlgo deployment found." "$RED"
        log_message "Looked at $SIMPLE_PATH and $DEPLOY_BASE" "$YELLOW"
        log_message "This script is for server deployments installed via install.sh" "$YELLOW"
        exit 1
    fi

    # Find all legacy deployments
    DEPLOYMENTS=()
    for dir in "$DEPLOY_BASE"/*/; do
        if [ -d "${dir}openalgo" ] && [ -f "${dir}openalgo/.env" ]; then
            deploy_name=$(basename "$dir")
            DEPLOYMENTS+=("$deploy_name")
        fi
    done

    if [ ${#DEPLOYMENTS[@]} -eq 0 ]; then
        log_message "Error: No OpenAlgo deployments found in $SIMPLE_PATH or $DEPLOY_BASE" "$RED"
        exit 1
    fi

    log_message "Found ${#DEPLOYMENTS[@]} legacy deployment(s):" "$GREEN"
    for i in "${!DEPLOYMENTS[@]}"; do
        log_message "  $((i+1)). ${DEPLOYMENTS[$i]}" "$BLUE"
    done

    if [ ${#DEPLOYMENTS[@]} -eq 1 ]; then
        SELECTED_DEPLOY="${DEPLOYMENTS[0]}"
        log_message "\nAuto-selected: $SELECTED_DEPLOY" "$GREEN"
    else
        echo ""
        while true; do
            read -p "Select deployment to change domain for (1-${#DEPLOYMENTS[@]}): " choice
            if [[ "$choice" =~ ^[0-9]+$ ]] && [ "$choice" -ge 1 ] && [ "$choice" -le ${#DEPLOYMENTS[@]} ]; then
                SELECTED_DEPLOY="${DEPLOYMENTS[$((choice-1))]}"
                break
            else
                log_message "Invalid choice." "$RED"
            fi
        done
    fi

    # Derive paths (legacy multi-deploy layout)
    BASE_PATH="$DEPLOY_BASE/$SELECTED_DEPLOY"
    OPENALGO_PATH="$BASE_PATH/openalgo"
    SOCKET_FILE="$BASE_PATH/openalgo.sock"
    SERVICE_NAME="openalgo-$SELECTED_DEPLOY"
    ENV_FILE="$OPENALGO_PATH/.env"
fi

# ============================================
# Step 3: Extract current domain from .env
# ============================================
log_message "\n--- Discovering current configuration ---" "$BLUE"

# Extract current domain from HOST_SERVER in .env
CURRENT_DOMAIN=""
if [ -f "$ENV_FILE" ]; then
    CURRENT_DOMAIN=$(sudo grep -oP "HOST_SERVER\s*=\s*'https?://\K[^']+" "$ENV_FILE" 2>/dev/null)
fi

if [ -z "$CURRENT_DOMAIN" ]; then
    log_message "Error: Could not extract current domain from $ENV_FILE" "$RED"
    log_message "Expected HOST_SERVER = 'https://yourdomain.com' in .env" "$YELLOW"
    exit 1
fi

log_message "Current domain: $CURRENT_DOMAIN" "$GREEN"

# ============================================
# Step 4: Discover all related config files
# ============================================

# Find Nginx config
NGINX_CONFIG_FILE=""
if [ -f "$NGINX_AVAILABLE/$CURRENT_DOMAIN.conf" ]; then
    NGINX_CONFIG_FILE="$NGINX_AVAILABLE/$CURRENT_DOMAIN.conf"
elif [ -f "$NGINX_AVAILABLE/$CURRENT_DOMAIN" ]; then
    NGINX_CONFIG_FILE="$NGINX_AVAILABLE/$CURRENT_DOMAIN"
fi

# Find SSL certificate
SSL_CERT_PATH=""
if [ -d "/etc/letsencrypt/live/$CURRENT_DOMAIN" ]; then
    SSL_CERT_PATH="/etc/letsencrypt/live/$CURRENT_DOMAIN"
fi

# Find systemd service
SERVICE_FILE=""
if [ -f "/etc/systemd/system/$SERVICE_NAME.service" ]; then
    SERVICE_FILE="/etc/systemd/system/$SERVICE_NAME.service"
fi

# Extract domain-related values from .env
CURRENT_HOST_SERVER=$(sudo grep -oP "HOST_SERVER\s*=\s*'\K[^']+" "$ENV_FILE" 2>/dev/null)
CURRENT_WEBSOCKET_URL=$(sudo grep -oP "WEBSOCKET_URL\s*=\s*'\K[^']+" "$ENV_FILE" 2>/dev/null)
CURRENT_REDIRECT_URL=$(sudo grep -oP "REDIRECT_URL\s*=\s*'\K[^']+" "$ENV_FILE" 2>/dev/null)
CURRENT_CORS_ORIGINS=$(sudo grep -oP "CORS_ALLOWED_ORIGINS\s*=\s*'\K[^']+" "$ENV_FILE" 2>/dev/null)

# ============================================
# Step 5: Display discovered configuration
# ============================================
log_message "\n========================================" "$YELLOW"
log_message "  Current Deployment Configuration" "$YELLOW"
log_message "========================================" "$YELLOW"
log_message "" ""
log_message "Deployment Name:    $SELECTED_DEPLOY" "$BLUE"
log_message "Install Path:       $OPENALGO_PATH" "$BLUE"
log_message "Service Name:       $SERVICE_NAME" "$BLUE"
log_message "Socket File:        $SOCKET_FILE" "$BLUE"
log_message "" ""
log_message "--- .env Settings ---" "$YELLOW"
log_message "HOST_SERVER:        $CURRENT_HOST_SERVER" "$BLUE"
log_message "WEBSOCKET_URL:      $CURRENT_WEBSOCKET_URL" "$BLUE"
log_message "REDIRECT_URL:       $CURRENT_REDIRECT_URL" "$BLUE"
log_message "CORS_ALLOWED_ORIGINS: $CURRENT_CORS_ORIGINS" "$BLUE"
log_message "" ""
log_message "--- Nginx ---" "$YELLOW"
if [ -n "$NGINX_CONFIG_FILE" ]; then
    log_message "Config File:        $NGINX_CONFIG_FILE" "$BLUE"
else
    log_message "Config File:        NOT FOUND (will create new)" "$RED"
fi
if [ "$NGINX_CONFIG_MODE" = "sites" ] && [ -n "$NGINX_CONFIG_FILE" ]; then
    SYMLINK="$NGINX_ENABLED/$(basename $NGINX_CONFIG_FILE)"
    if [ -L "$SYMLINK" ]; then
        log_message "Sites-Enabled:      $SYMLINK (symlink exists)" "$BLUE"
    else
        log_message "Sites-Enabled:      NOT FOUND" "$RED"
    fi
fi
log_message "" ""
log_message "--- SSL Certificate ---" "$YELLOW"
if [ -n "$SSL_CERT_PATH" ]; then
    log_message "Certificate Path:   $SSL_CERT_PATH" "$BLUE"
    # Show certificate expiry
    CERT_EXPIRY=$(sudo openssl x509 -enddate -noout -in "$SSL_CERT_PATH/fullchain.pem" 2>/dev/null | cut -d= -f2)
    if [ -n "$CERT_EXPIRY" ]; then
        log_message "Certificate Expiry: $CERT_EXPIRY" "$BLUE"
    fi
else
    log_message "Certificate Path:   NOT FOUND" "$RED"
fi
log_message "" ""
log_message "--- Systemd Service ---" "$YELLOW"
if [ -n "$SERVICE_FILE" ]; then
    SERVICE_STATUS=$(sudo systemctl is-active "$SERVICE_NAME" 2>/dev/null)
    log_message "Service File:       $SERVICE_FILE" "$BLUE"
    log_message "Service Status:     $SERVICE_STATUS" "$BLUE"
else
    log_message "Service File:       NOT FOUND" "$RED"
fi
log_message "========================================" "$YELLOW"

# ============================================
# Step 6: Get new domain from user
# ============================================
echo ""
while true; do
    read -p "Enter the NEW domain name (e.g., newalgo.example.com): " NEW_DOMAIN
    if [ -z "$NEW_DOMAIN" ]; then
        log_message "Error: Domain name is required" "$RED"
        continue
    fi
    # Domain validation (same as install.sh)
    if [[ ! $NEW_DOMAIN =~ ^[a-zA-Z0-9]([a-zA-Z0-9-]*[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9-]*[a-zA-Z0-9])?)*\.[a-zA-Z]{2,}$ ]]; then
        log_message "Error: Invalid domain format. Please enter a valid domain name" "$RED"
        continue
    fi
    if [ "$NEW_DOMAIN" = "$CURRENT_DOMAIN" ]; then
        log_message "Error: New domain is the same as the current domain" "$RED"
        continue
    fi
    break
done

# Check if it's a subdomain
if [[ $NEW_DOMAIN =~ ^[^.]+\.[^.]+\.[^.]+$ ]]; then
    IS_SUBDOMAIN=true
else
    IS_SUBDOMAIN=false
fi

# ============================================
# Step 7: Show changes and ask for confirmation
# ============================================
log_message "\n========================================" "$YELLOW"
log_message "  Planned Changes" "$YELLOW"
log_message "========================================" "$YELLOW"
log_message "" ""
log_message "Domain Change: $CURRENT_DOMAIN  -->  $NEW_DOMAIN" "$GREEN"
log_message "" ""
log_message "--- .env Updates ---" "$YELLOW"
log_message "HOST_SERVER:          https://$CURRENT_DOMAIN  -->  https://$NEW_DOMAIN" "$BLUE"
log_message "WEBSOCKET_URL:        wss://$CURRENT_DOMAIN/ws  -->  wss://$NEW_DOMAIN/ws" "$BLUE"
if echo "$CURRENT_REDIRECT_URL" | grep -q "$CURRENT_DOMAIN"; then
    log_message "REDIRECT_URL:         .../$CURRENT_DOMAIN/...  -->  .../$NEW_DOMAIN/..." "$BLUE"
fi
if echo "$CURRENT_CORS_ORIGINS" | grep -q "$CURRENT_DOMAIN"; then
    log_message "CORS_ALLOWED_ORIGINS: https://$CURRENT_DOMAIN  -->  https://$NEW_DOMAIN" "$BLUE"
fi
log_message "" ""
log_message "--- Nginx ---" "$YELLOW"
NEW_NGINX_CONFIG="$NGINX_AVAILABLE/$NEW_DOMAIN.conf"
if [ -n "$NGINX_CONFIG_FILE" ]; then
    log_message "Rename:  $(basename $NGINX_CONFIG_FILE)  -->  $NEW_DOMAIN.conf" "$BLUE"
else
    log_message "Create:  $NEW_NGINX_CONFIG" "$BLUE"
fi
log_message "Update:  server_name, ssl_certificate paths" "$BLUE"
log_message "" ""
log_message "--- SSL Certificate ---" "$YELLOW"
log_message "Obtain new Let's Encrypt certificate for: $NEW_DOMAIN" "$BLUE"
log_message "" ""
log_message "--- Services ---" "$YELLOW"
log_message "Stop:    $SERVICE_NAME (before changes)" "$BLUE"
log_message "Restart: $SERVICE_NAME + nginx (after changes)" "$BLUE"
log_message "" ""
log_message "--- Broker Redirect URL ---" "$YELLOW"
# Extract broker from redirect URL or deploy name
BROKER_NAME=$(echo "$CURRENT_REDIRECT_URL" | grep -oP 'https?://[^/]+/\K[^/]+')
if [ -n "$BROKER_NAME" ]; then
    log_message "Update your broker developer portal redirect URL to:" "$YELLOW"
    log_message "  https://$NEW_DOMAIN/$BROKER_NAME/callback" "$GREEN"
fi
log_message "" ""
log_message "Note: The deployment directory ($SELECTED_DEPLOY) and" "$YELLOW"
log_message "service name ($SERVICE_NAME) will NOT be renamed." "$YELLOW"
log_message "This is cosmetic only and does not affect functionality." "$YELLOW"
log_message "========================================" "$YELLOW"

echo ""
read -p "Do you want to proceed with these changes? (y/n): " confirm
if [[ ! $confirm =~ ^[Yy]$ ]]; then
    log_message "Domain change cancelled by user." "$YELLOW"
    exit 0
fi

# ============================================
# Step 8: Stop the service
# ============================================
log_message "\n[Step 1/6] Stopping service: $SERVICE_NAME..." "$BLUE"
if sudo systemctl is-active --quiet "$SERVICE_NAME" 2>/dev/null; then
    sudo systemctl stop "$SERVICE_NAME"
    check_status "Failed to stop $SERVICE_NAME"
    log_message "Service stopped successfully" "$GREEN"
else
    log_message "Service is not currently running" "$YELLOW"
fi

# ============================================
# Step 9: Backup current configs
# ============================================
log_message "\n[Step 2/6] Backing up current configuration..." "$BLUE"

BACKUP_DIR="$OPENALGO_PATH/db/domain_change_backup_${TIMESTAMP}"
sudo mkdir -p "$BACKUP_DIR"

# Backup .env
sudo cp "$ENV_FILE" "$BACKUP_DIR/.env.backup"
log_message "  Backed up: .env" "$GREEN"

# Backup nginx config
if [ -n "$NGINX_CONFIG_FILE" ] && [ -f "$NGINX_CONFIG_FILE" ]; then
    sudo cp "$NGINX_CONFIG_FILE" "$BACKUP_DIR/nginx_$(basename $NGINX_CONFIG_FILE).backup"
    log_message "  Backed up: nginx config" "$GREEN"
fi

log_message "Backup location: $BACKUP_DIR" "$GREEN"

# ============================================
# Step 10: Update .env file
# ============================================
log_message "\n[Step 3/6] Updating .env file..." "$BLUE"

# Replace all occurrences of old domain with new domain in .env
sudo sed -i "s|$CURRENT_DOMAIN|$NEW_DOMAIN|g" "$ENV_FILE"

# Explicitly ensure critical variables are correct
sudo sed -i "s|HOST_SERVER = '.*'|HOST_SERVER = 'https://$NEW_DOMAIN'|g" "$ENV_FILE"
sudo sed -i "s|WEBSOCKET_URL='.*'|WEBSOCKET_URL='wss://$NEW_DOMAIN/ws'|g" "$ENV_FILE"
# Handle WEBSOCKET_URL with spaces around =
sudo sed -i "s|WEBSOCKET_URL = '.*'|WEBSOCKET_URL = 'wss://$NEW_DOMAIN/ws'|g" "$ENV_FILE"
check_status "Failed to update .env file"

# Verify the changes
VERIFY_HOST=$(sudo grep -oP "HOST_SERVER\s*=\s*'\K[^']+" "$ENV_FILE")
VERIFY_WS=$(sudo grep -oP "WEBSOCKET_URL\s*=\s*'\K[^']+" "$ENV_FILE")
log_message "  HOST_SERVER:    $VERIFY_HOST" "$GREEN"
log_message "  WEBSOCKET_URL:  $VERIFY_WS" "$GREEN"
log_message ".env updated successfully" "$GREEN"

# ============================================
# Step 11: Set up temporary Nginx for Certbot
# ============================================
log_message "\n[Step 4/6] Obtaining SSL certificate for $NEW_DOMAIN..." "$BLUE"

# Remove old nginx config and symlinks
if [ -n "$NGINX_CONFIG_FILE" ] && [ -f "$NGINX_CONFIG_FILE" ]; then
    sudo rm -f "$NGINX_CONFIG_FILE"
fi
if [ "$NGINX_CONFIG_MODE" = "sites" ]; then
    sudo rm -f "$NGINX_ENABLED/$CURRENT_DOMAIN.conf"
    sudo rm -f "$NGINX_ENABLED/$CURRENT_DOMAIN"
fi

# Create temporary Nginx config for certbot HTTP challenge
sudo tee "$NEW_NGINX_CONFIG" > /dev/null << EOL
server {
    listen 80;
    listen [::]:80;
    server_name $NEW_DOMAIN;
    root /var/www/html;

    location / {
        try_files \$uri \$uri/ =404;
    }
}
EOL

# Enable the temporary config
if [ "$NGINX_CONFIG_MODE" = "sites" ]; then
    sudo ln -sf "$NEW_NGINX_CONFIG" "$NGINX_ENABLED/"
fi

# Reload nginx with temporary config
sudo nginx -t
check_status "Failed to validate temporary Nginx configuration"
sudo systemctl reload nginx
check_status "Failed to reload Nginx"

# Obtain new SSL certificate
log_message "Running Certbot for $NEW_DOMAIN..." "$BLUE"
if [ "$IS_SUBDOMAIN" = true ]; then
    sudo certbot --nginx -d "$NEW_DOMAIN" --non-interactive --agree-tos --email admin@${NEW_DOMAIN#*.}
else
    sudo certbot --nginx -d "$NEW_DOMAIN" -d "www.$NEW_DOMAIN" --non-interactive --agree-tos --email admin@$NEW_DOMAIN
fi

# Verify certificate was obtained
if [ ! -f "/etc/letsencrypt/live/$NEW_DOMAIN/fullchain.pem" ]; then
    log_message "Error: Failed to obtain SSL certificate for $NEW_DOMAIN" "$RED"
    log_message "" ""
    log_message "Possible causes:" "$YELLOW"
    log_message "  1. DNS for $NEW_DOMAIN does not point to this server's IP" "$YELLOW"
    log_message "  2. Port 80 is not reachable from the internet" "$YELLOW"
    log_message "  3. Let's Encrypt rate limit reached" "$YELLOW"
    log_message "" ""
    log_message "Restoring backup..." "$YELLOW"
    sudo cp "$BACKUP_DIR/.env.backup" "$ENV_FILE"
    if [ -f "$BACKUP_DIR/nginx_"*".backup" ]; then
        sudo cp "$BACKUP_DIR/nginx_"*".backup" "$NGINX_CONFIG_FILE"
        if [ "$NGINX_CONFIG_MODE" = "sites" ]; then
            sudo rm -f "$NGINX_ENABLED/$(basename $NEW_NGINX_CONFIG)"
            sudo ln -sf "$NGINX_CONFIG_FILE" "$NGINX_ENABLED/"
        fi
    fi
    sudo rm -f "$NEW_NGINX_CONFIG"
    sudo nginx -t && sudo systemctl reload nginx
    sudo systemctl start "$SERVICE_NAME" 2>/dev/null
    log_message "Backup restored. Original configuration is active." "$GREEN"
    exit 1
fi
log_message "SSL certificate obtained successfully" "$GREEN"

# ============================================
# Step 12: Write final Nginx config
# ============================================
log_message "\n[Step 5/6] Configuring final Nginx setup..." "$BLUE"

# Remove the temporary config
sudo rm -f "$NEW_NGINX_CONFIG"
if [ "$NGINX_CONFIG_MODE" = "sites" ]; then
    sudo rm -f "$NGINX_ENABLED/$(basename $NEW_NGINX_CONFIG)"
fi

# Write full production nginx config
sudo tee "$NEW_NGINX_CONFIG" > /dev/null << EOL
server {
    listen 80;
    listen [::]:80;
    server_name $NEW_DOMAIN;

    # WebSocket path exceptions to avoid 301 redirect loop
    location = /ws {
        return 301 https://\$host\$request_uri;
    }

    location /ws/ {
        return 301 https://\$host\$request_uri;
    }

    # All other HTTP requests get redirected to HTTPS
    location / {
        return 301 https://\$host\$request_uri;
    }
}

server {
    listen 443 ssl;
    listen [::]:443 ssl;

    server_name $NEW_DOMAIN;

    ssl_certificate /etc/letsencrypt/live/$NEW_DOMAIN/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/$NEW_DOMAIN/privkey.pem;

    # SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers on;
    ssl_ciphers EECDH+AESGCM:EDH+AESGCM;
    ssl_ecdh_curve secp384r1;
    ssl_session_timeout 10m;
    ssl_session_cache shared:SSL:10m;
    ssl_session_tickets off;
    ssl_stapling on;
    ssl_stapling_verify on;

    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=63072000" always;

    # WebSocket without trailing slash
    location = /ws {
        proxy_pass http://127.0.0.1:8765;
        proxy_http_version 1.1;

        # Extended timeouts for long-running connections (up to 24 hours)
        proxy_read_timeout 86400s;
        proxy_send_timeout 86400s;

        # Disable proxy buffering for real-time data
        proxy_buffering off;

        # WebSocket headers
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";

        # Other headers
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_set_header X-Forwarded-Host \$host;
    }

    # WebSocket with trailing slash
    location /ws/ {
        proxy_pass http://127.0.0.1:8765/;
        proxy_http_version 1.1;

        # Extended timeouts for long-running connections (up to 24 hours)
        proxy_read_timeout 86400s;
        proxy_send_timeout 86400s;

        # Disable proxy buffering for real-time data
        proxy_buffering off;

        # WebSocket headers
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";

        # Other headers
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_set_header X-Forwarded-Host \$host;
    }

    # Socket.IO (Flask-SocketIO real-time events)
    location /socket.io/ {
        proxy_pass http://unix:$SOCKET_FILE;
        proxy_http_version 1.1;

        # Extended timeouts for long-lived Socket.IO sessions
        proxy_read_timeout 86400s;
        proxy_send_timeout 86400s;

        # Disable proxy buffering for real-time events
        proxy_buffering off;

        # WebSocket upgrade headers (required for Socket.IO WebSocket transport)
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";

        # Other headers
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_set_header X-Forwarded-Host \$host;
    }

    # Main app (Gunicorn UDS)
    location / {
        proxy_pass http://unix:$SOCKET_FILE;
        proxy_http_version 1.1;

        # Extended timeouts for broker authentication (cold start can take 60-90s)
        proxy_read_timeout 300s;
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;

        # Increased buffer sizes for large headers (auth tokens, session cookies)
        proxy_buffer_size 128k;
        proxy_buffers 4 256k;
        proxy_busy_buffers_size 256k;

        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_redirect off;
    }
}
EOL

# Enable the new config
if [ "$NGINX_CONFIG_MODE" = "sites" ]; then
    sudo ln -sf "$NEW_NGINX_CONFIG" "$NGINX_ENABLED/"
fi

# Test nginx configuration
sudo nginx -t
check_status "Failed to validate final Nginx configuration"
log_message "Nginx configuration updated successfully" "$GREEN"

# ============================================
# Step 13: Restart services
# ============================================
log_message "\n[Step 6/6] Restarting services..." "$BLUE"

sudo systemctl reload nginx
check_status "Failed to reload Nginx"
log_message "Nginx reloaded" "$GREEN"

sudo systemctl start "$SERVICE_NAME"
check_status "Failed to start $SERVICE_NAME"
log_message "Service $SERVICE_NAME started" "$GREEN"

# Verify service is running
sleep 3
if sudo systemctl is-active --quiet "$SERVICE_NAME"; then
    log_message "Service $SERVICE_NAME is running" "$GREEN"
else
    log_message "Warning: Service $SERVICE_NAME may not have started correctly" "$RED"
    log_message "Check logs with: sudo journalctl -u $SERVICE_NAME -n 50" "$YELLOW"
fi

# ============================================
# Summary
# ============================================
log_message "\n========================================" "$GREEN"
log_message "  Domain Change Summary" "$GREEN"
log_message "========================================" "$GREEN"
log_message "" ""
log_message "Domain Changed:  $CURRENT_DOMAIN  -->  $NEW_DOMAIN" "$GREEN"
log_message "" ""
log_message "Updated Files:" "$BLUE"
log_message "  .env:          $ENV_FILE" "$BLUE"
log_message "  Nginx:         $NEW_NGINX_CONFIG" "$BLUE"
log_message "  SSL Cert:      /etc/letsencrypt/live/$NEW_DOMAIN/" "$BLUE"
log_message "" ""
log_message "Backup Location: $BACKUP_DIR" "$BLUE"
log_message "Change Log:      $LOG_FILE" "$BLUE"
log_message "" ""

if [ -n "$BROKER_NAME" ]; then
    log_message "========================================" "$RED"
    log_message "  ACTION REQUIRED: Update Broker Portal" "$RED"
    log_message "========================================" "$RED"
    log_message "" ""
    log_message "Update your broker's developer portal redirect URL to:" "$YELLOW"
    log_message "  https://$NEW_DOMAIN/$BROKER_NAME/callback" "$GREEN"
    log_message "" ""
    log_message "Without this change, broker login/authentication will fail!" "$RED"
    log_message "" ""
fi

log_message "Your OpenAlgo instance is now available at:" "$GREEN"
log_message "  https://$NEW_DOMAIN" "$GREEN"
log_message "" ""

log_message "Useful Commands:" "$YELLOW"
log_message "  Check status:  sudo systemctl status $SERVICE_NAME" "$BLUE"
log_message "  View logs:     sudo journalctl -u $SERVICE_NAME -n 50" "$BLUE"
log_message "  Restart:       sudo systemctl restart $SERVICE_NAME" "$BLUE"
log_message "" ""
log_message "Domain change completed successfully!" "$GREEN"

```


---

# FILE: install\Docker-install-readme.md

```md
# OpenAlgo Docker Installation

> **Advanced Users**: For multi-instance deployment with custom SSL (wildcard certificates) and Portainer, see [Docker-Multi-SSL-README.md](./Docker-Multi-SSL-README.md)

## Desktop Installation (Windows/macOS/Linux)

For **personal trading** on your desktop/laptop with Docker Desktop.

### Prerequisites

1. **Install Docker Desktop**
   - Windows: https://docs.docker.com/desktop/install/windows-install/
   - macOS: https://docs.docker.com/desktop/install/mac-install/
   - Linux: https://docs.docker.com/desktop/install/linux-install/

2. **Start Docker Desktop** and wait for it to fully initialize

### Quick Start (2 Commands)

#### Windows (PowerShell or Command Prompt)
```powershell
curl.exe -O https://raw.githubusercontent.com/marketcalls/openalgo/main/install/docker-run.bat
docker-run.bat
```

#### macOS / Linux (Terminal)
```bash
curl -O https://raw.githubusercontent.com/marketcalls/openalgo/main/install/docker-run.sh
chmod +x docker-run.sh
./docker-run.sh
```

### What Happens

1. Sets up in the **current directory** (where the script is located)
2. Downloads configuration template from GitHub
3. Generates secure APP_KEY and API_KEY_PEPPER
4. Prompts for broker name (with validation)
5. Prompts for API credentials
6. For **XTS brokers** (fivepaisaxts, compositedge, ibulls, iifl, jainamxts, rmoney, wisdom): prompts for market data credentials
7. Pulls and starts the Docker container
8. **Runs database migrations automatically** on startup

### After Setup

- **Web UI**: http://127.0.0.1:5000
- **WebSocket**: ws://127.0.0.1:8765
- **Config file**: `.env` (in script directory)
- **Database**: `db/` (in script directory)
- **Strategies**: `strategies/` (Python strategy scripts)
- **Logs**: `log/` (application and strategy logs)

### Management Commands

```bash
# Windows
docker-run.bat start     # Start OpenAlgo
docker-run.bat stop      # Stop OpenAlgo
docker-run.bat restart   # Restart (pulls latest + auto-migrates)
docker-run.bat logs      # View live logs
docker-run.bat status    # Check if running
docker-run.bat pull      # Pull latest image
docker-run.bat migrate   # Run database migrations manually
docker-run.bat shell     # Open bash shell in container
docker-run.bat setup     # Re-run setup (regenerate keys)

# macOS / Linux
./docker-run.sh start
./docker-run.sh stop
./docker-run.sh restart
./docker-run.sh logs
./docker-run.sh status
./docker-run.sh pull
./docker-run.sh migrate
./docker-run.sh shell
./docker-run.sh setup
```

### Updating OpenAlgo

Database migrations run **automatically** when the container starts.

```bash
# Windows - Pull latest and restart (auto-migrates)
docker-run.bat restart

# macOS/Linux - Pull latest and restart (auto-migrates)
./docker-run.sh restart

# Or step by step:
docker-run.bat pull      # Pull latest image
docker-run.bat restart   # Restart with new image

# Manual migration (if needed)
docker-run.bat migrate
```

### File Permissions

The scripts automatically handle file permissions:

- **db/** directory: Created with write access for the container
- **strategies/** directory: Python strategy scripts (persisted locally)
- **log/** directory: Application and strategy logs (persisted locally)
- **.env** file: Read-only mount inside container (`:ro`)
- **Container user**: Runs as non-root user `appuser` (UID 1000)

If you encounter permission issues on Linux:
```bash
# Fix directory permissions
sudo chown -R 1000:1000 db/ strategies/ log/
chmod -R 755 db/ strategies/ log/
```

### XTS Brokers

These brokers require **additional market data credentials**:
- fivepaisaxts
- compositedge
- ibulls
- iifl
- jainamxts
- rmoney
- wisdom

The setup script will automatically prompt for these credentials when you select an XTS broker.

---

## Server Installation (Ubuntu/Debian with SSL)

For **production deployment** on a cloud server with custom domain and SSL certificate.

### Quick Start

This script provides a simplified, automated installation of OpenAlgo using Docker on Ubuntu/Debian systems with custom domain and SSL.

### One-Line Installation

```bash
wget https://raw.githubusercontent.com/marketcalls/openalgo/refs/heads/main/install/install-docker.sh && chmod +x install-docker.sh && ./install-docker.sh
```

### Prerequisites

- Fresh Ubuntu 20.04+ or Debian 11+ server
- Root access OR non-root user with sudo privileges
- Domain name pointed to your server IP
- Server with at least 1GB RAM (2GB recommended)

### Installation Steps

#### Option 1: As Non-Root User (Recommended)

```bash
# If you're logged in as root, create a non-root user first
adduser openalgo
usermod -aG sudo openalgo
su - openalgo

# Download and run the script
wget https://raw.githubusercontent.com/marketcalls/openalgo/refs/heads/main/install/install-docker.sh
chmod +x install-docker.sh
./install-docker.sh
```

#### Option 2: As Root User

```bash
# Download and run directly
wget https://raw.githubusercontent.com/marketcalls/openalgo/refs/heads/main/install/install-docker.sh
chmod +x install-docker.sh
./install-docker.sh
# (Confirm when prompted to proceed as root)
```

**Note:** While the script works as root, using a non-root user is recommended for better security in production environments.

### Follow the Prompts

The script will ask you for:
- Domain name (e.g., demo.openalgo.in)
- Broker name from the supported list
- Broker API credentials (key and secret)
- Market data credentials (for XTS brokers only)
- Email for SSL certificate notifications
- Confirmation to proceed

### What the Script Does

1. ✅ Updates system packages
2. ✅ Installs Docker & Docker Compose
3. ✅ Installs Nginx web server
4. ✅ Installs Certbot for SSL
5. ✅ Clones OpenAlgo repository to `/opt/openalgo`
6. ✅ Configures environment variables
7. ✅ Sets up firewall (UFW)
8. ✅ Obtains SSL certificate from Let's Encrypt
9. ✅ Configures Nginx with SSL and WebSocket support
10. ✅ Builds and starts Docker container
11. ✅ Creates management helper scripts

**Installation typically takes 5-10 minutes.**

### After Installation

1. Visit `https://yourdomain.com` in your browser
2. Create your admin account
3. Login to OpenAlgo
4. Complete broker authentication using OAuth

### Management Commands

The installation creates these helper commands:

```bash
# View application status
openalgo-status

# View live logs (follow mode)
openalgo-logs

# Restart application
openalgo-restart

# Create backup
openalgo-backup
```

### Docker Commands

```bash
# Navigate to installation directory
cd /opt/openalgo

# Restart container
sudo docker compose restart

# Stop container
sudo docker compose stop

# Start container
sudo docker compose start

# View logs
sudo docker compose logs -f

# Rebuild from scratch
sudo docker compose down
sudo docker compose build --no-cache
sudo docker compose up -d
```

### File Locations

| Item | Location |
|------|----------|
| Installation | `/opt/openalgo` |
| Configuration | `/opt/openalgo/.env` |
| Database | Docker volume `openalgo_db` |
| Strategies | Docker volume `openalgo_strategies` |
| Application Logs | `/opt/openalgo/log` |
| Nginx Config | `/etc/nginx/sites-available/yourdomain.com` |
| SSL Certificates | `/etc/letsencrypt/live/yourdomain.com/` |
| Backups | `/opt/openalgo-backups/` |

### Updating OpenAlgo

Database migrations run **automatically** when the container starts.

```bash
cd /opt/openalgo

# Create backup first
openalgo-backup

# Stop container
sudo docker compose down

# Pull latest code
sudo git pull origin main

# Rebuild and restart (migrations run automatically)
sudo docker compose build --no-cache
sudo docker compose up -d

# Verify
openalgo-status

# Manual migration (if needed)
sudo docker compose exec web python /app/upgrade/migrate_all.py
```

### Troubleshooting

**Container not starting:**
```bash
# Check container status
sudo docker ps -a

# View detailed logs
sudo docker compose logs -f

# Check container health
sudo docker inspect openalgo-web --format='{{.State.Health.Status}}'
```

**Permission errors with logs:**
```bash
# Fix log directory permissions
cd /opt/openalgo
sudo chown -R 1000:1000 log
sudo docker compose restart
```

**WebSocket connection issues:**
```bash
# Check if ports are listening
sudo netstat -tlnp | grep -E ':(5000|8765)'

# Test WebSocket connection
curl -i -N \
  -H "Connection: Upgrade" \
  -H "Upgrade: websocket" \
  https://yourdomain.com/ws
```

**Nginx issues:**
```bash
# Test configuration
sudo nginx -t

# View error logs
sudo tail -f /var/log/nginx/yourdomain.com_error.log

# Restart Nginx
sudo systemctl restart nginx
```

**SSL certificate issues:**
```bash
# Test renewal
sudo certbot renew --dry-run

# Force renewal
sudo certbot renew --force-renewal

# Check certificate status
sudo certbot certificates
```

**Docker issues:**
```bash
# Check Docker status
sudo systemctl status docker

# Restart Docker
sudo systemctl restart docker

# View Docker logs
sudo journalctl -u docker -f
```

### Firewall Configuration

The script automatically configures UFW:
- **Port 22** (SSH) - Open
- **Port 80** (HTTP) - Open (for SSL renewal)
- **Port 443** (HTTPS) - Open
- **Ports 5000, 8765** - Only accessible via localhost (Docker ports)

### Security Best Practices

1. **Change default credentials** immediately after first login
2. **Keep system updated**: 
   ```bash
   sudo apt update && sudo apt upgrade -y
   ```
3. **Monitor logs regularly**:
   ```bash
   openalgo-logs
   ```
4. **Setup automated backups**: Create a cron job
   ```bash
   # Backup daily at 2 AM
   crontab -e
   # Add: 0 2 * * * /usr/local/bin/openalgo-backup
   ```
5. **Use strong passwords** for your OpenAlgo account
6. **Never share broker credentials** with anyone
7. **Review firewall rules periodically**:
   ```bash
   sudo ufw status
   ```

### Cloudflare Setup (Optional)

For additional security and CDN benefits:

1. **Add domain to Cloudflare**
   - Sign up at cloudflare.com
   - Add your domain

2. **Update DNS**
   - In Cloudflare DNS settings:
   - Create A record pointing to your server IP
   - Enable proxy (orange cloud icon)

3. **Configure SSL/TLS**
   - Go to SSL/TLS settings
   - Set mode to **"Full (strict)"**
   - Enable "Always Use HTTPS"

4. **Enable WebSockets**
   - Go to Network settings
   - Enable "WebSockets"
   - Enable "HTTP/2"

5. **Security Settings** (Optional)
   - Enable "Under Attack Mode" if needed
   - Set up Page Rules for caching
   - Configure Firewall Rules

### Backup and Restore

**Create Backup:**
```bash
openalgo-backup
```
Backups are stored in `/opt/openalgo-backups/` and include:
- Database
- Configuration (.env file)
- Strategy files
- Last 7 backups are kept automatically

**Restore from Backup:**
```bash
# Stop container
cd /opt/openalgo
sudo docker compose stop

# Extract backup (replace TIMESTAMP with actual value)
sudo tar -xzf /opt/openalgo-backups/openalgo_backup_TIMESTAMP.tar.gz -C /opt/openalgo

# Fix permissions
sudo chown -R 1000:1000 log

# Start container
sudo docker compose start

# Verify
openalgo-status
```

### Complete Uninstallation

```bash
# Stop and remove container
cd /opt/openalgo
sudo docker compose down -v

# Remove installation directory
sudo rm -rf /opt/openalgo

# Remove backups (optional)
sudo rm -rf /opt/openalgo-backups

# Remove Nginx configuration
sudo rm /etc/nginx/sites-available/yourdomain.com
sudo rm /etc/nginx/sites-enabled/yourdomain.com
sudo systemctl reload nginx

# Remove SSL certificate
sudo certbot delete --cert-name yourdomain.com

# Remove management scripts
sudo rm /usr/local/bin/openalgo-*

# Optional: Remove Docker (if not needed for other apps)
sudo apt remove -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
sudo rm -rf /var/lib/docker
```

### Getting Help

- **Documentation**: https://docs.openalgo.in
- **Discord Community**: https://discord.com/invite/UPh7QPsNhP
- **GitHub Issues**: https://github.com/marketcalls/openalgo/issues
- **YouTube Tutorials**: https://youtube.com/@openalgoHQ
- **Website**: https://openalgo.in

### Supported Brokers

| Broker | Code | XTS API |
|--------|------|---------|
| 5paisa | `fivepaisa` | No |
| 5paisa XTS | `fivepaisaxts` | Yes |
| AliceBlue | `aliceblue` | No |
| Angel One | `angel` | No |
| Compositedge | `compositedge` | Yes |
| Definedge | `definedge` | No |
| Delta Exchange | `deltaexchange` | No |
| Dhan | `dhan` | No |
| Dhan Sandbox | `dhan_sandbox` | No |
| Firstock | `firstock` | No |
| Flattrade | `flattrade` | No |
| Fyers | `fyers` | No |
| Groww | `groww` | No |
| IBulls | `ibulls` | Yes |
| IIFL | `iifl` | Yes |
| Iiflcapital | `iiflcapital` | No |
| IndMoney | `indmoney` | No |
| Jainam XTS | `jainamxts` | Yes |
| Kotak | `kotak` | No |
| Motilal Oswal | `motilal` | No |
| MStock | `mstock` | No |
| Nubra | `nubra` | No |
| Paytm Money | `paytm` | No |
| Pocketful | `pocketful` | No |
| RMoney | `rmoney` | Yes |
| Samco | `samco` | No |
| Shoonya | `shoonya` | No |
| Tradejini | `tradejini` | No |
| Upstox | `upstox` | No |
| Wisdom Capital | `wisdom` | Yes |
| Zebu | `zebu` | No |
| Zerodha | `zerodha` | No |

**Note:** XTS API brokers require additional market data API credentials during installation.

### System Requirements

**Minimum:**
- 1 vCPU
- 1GB RAM
- 10GB disk space
- Ubuntu 20.04+ or Debian 11+
- Internet connection

**Recommended:**
- 2 vCPU
- 2GB RAM
- 20GB SSD storage
- Ubuntu 22.04 LTS
- Stable internet connection

### Architecture

```
┌─────────────────┐
│   Internet      │
└────────┬────────┘
         │ HTTPS (443)
         │
┌────────▼────────┐
│   Nginx         │ ← SSL/TLS, Rate Limiting
│   Reverse Proxy │
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
    ▼         ▼
┌───────┐ ┌──────────┐
│ Flask │ │WebSocket │ ← Docker Container
│ :5000 │ │  :8765   │   (openalgo-web)
└───────┘ └──────────┘
    │
    ▼
┌──────────┐
│ SQLite   │ ← Docker Volume
│ Database │   (openalgo_db)
└──────────┘
```

### FAQ

**Q: Can I use this on a server with existing Nginx?**
A: Yes, but you may need to manually merge configurations to avoid conflicts.

**Q: Can I use a different port instead of 443?**
A: Yes, but you'll need to modify the Nginx configuration manually.

**Q: Will this work with a subdomain?**
A: Yes, the script supports both root domains and subdomains.

**Q: Can I run multiple OpenAlgo instances?**
A: Not with this script. Each installation assumes it's the only instance.

**Q: How do I change my broker after installation?**
A: Edit `/opt/openalgo/.env`, update broker credentials, then run `sudo docker compose restart`.

**Q: Is my broker data secure?**
A: Yes, all data is encrypted in transit (HTTPS/WSS) and stored locally on your server.

**Q: Can I use this in production?**
A: Yes, this script is designed for production use with SSL, security headers, and proper firewall configuration.

**Q: What if my domain doesn't have an A record yet?**
A: Wait for DNS propagation (usually 5-60 minutes) before running the script.

### Changelog

**Version 1.1.0** (October 19, 2024)
- Added support for running as root user (with warning)
- Fixed permission issues with docker-compose.yaml creation
- Improved error handling
- Enhanced management scripts

**Version 1.0.0** (Initial Release)
- Complete automated installation
- SSL certificate automation
- Docker containerization
- Management helper scripts

### License

OpenAlgo is released under the **AGPL V3.0 License**.

### Contributing

Contributions are welcome! Please see our [Contributing Guide](../CONTRIBUTING.md).

---

**Note**: This script is designed for fresh server installations. If you have an existing OpenAlgo installation or other applications on the server, please review the script and make necessary adjustments to avoid conflicts.

For production deployments, we strongly recommend:
1. Using a non-root user
2. Setting up automated backups
3. Monitoring logs regularly
4. Keeping the system updated
5. Using Cloudflare or similar CDN/DDoS protection

**Need help?** Join our [Discord community](https://discord.com/invite/UPh7QPsNhP) for support and discussions!

```


---

# FILE: install\Docker-Multi-SSL-README.md

```md
# OpenAlgo Advanced Docker Installation (Multi-Instance & Custom SSL)

This guide covers the advanced installation script (`install-docker-multi-custom-ssl.sh`), which is designed for power users who need:
- **Multiple OpenAlgo instances** on a single server.
- **Custom SSL Certificates** (e.g., Wildcard SSLs).
- **Portainer** for container management.
- **Robust Healthchecks** and automatic error recovery.

## Quick Start

Run the following command on your Ubuntu 20.04+ or Debian 11+ server:

```bash
wget https://raw.githubusercontent.com/marketcalls/openalgo/main/install/install-docker-multi-custom-ssl.sh
chmod +x install-docker-multi-custom-ssl.sh
./install-docker-multi-custom-ssl.sh
```

## Prerequisites

- **OS**: Ubuntu 20.04+ LTS (Recommended: Ubuntu 24.04 LTS for Azure ARM64)
- **Permissions**: Root access or `sudo` privileges.
- **Domain**: A valid domain pointed to your server IP.
- **Ports**: 80, 443 (Server), 9000 (Portainer - Optional), 22 (SSH).

## Installation Features

When you run the script, it will interactively prompt you for:

1.  **Instance Name**:
    - You can give each installation a unique name (e.g., `algo1`, `fyers-bot`).
    - This allows you to run multiple independent copies of OpenAlgo side-by-side.

2.  **Domain & Broker**:
    - Choose your domain (e.g., `bot1.example.com`).
    - Select your broker and provide API credentials.

3.  **SSL Configuration**:
    - **Let's Encrypt**: Auto-generate free SSL certificates.
    - **Custom SSL**: Provide paths to your existing `.pem` and `.key` files (Great for Wildcard SSLs).

4.  **Portainer Management UI**:
    - Option to install Portainer to manage your Docker containers visually.
    - Can be exposed on a subdomain (e.g., `portainer.example.com`) or via IP (`http://IP:9000`).

## Setting Up Portainer (Important)

If you chose to install Portainer, follow these steps immediately after installation:

1.  **Access Portainer**:
    - Open your browser and navigate to the domain you configured (e.g., `https://portainer.example.com`) or `http://YOUR_SERVER_IP:9000`.

2.  **Create Admin User**:
    - You will be asked to create an initial admin username and password.
    - **Note:** For security, Portainer creates a timeout window for this initial setup.

### **Restarting Portainer (If Setup Times Out)**

If you wait too long to configure Portainer after installation, you may be locked out of the initial setup screen. To fix this, you must restart the container to reset the setup window:

```bash
# Restart the Portainer container
docker restart portainer
```

After running this command, refresh your browser immediately and set up your username and password.

## Managing Multiple Instances

Since this script supports multiple instances, docker compose commands need to be run in the specific instance directory.

**Directory Structure:**
```
/opt/
  ├── openalgo-algo1/       # Instance 1
  │   ├── docker-compose.yaml
  │   └── .env
  └── openalgo-fyers-bot/   # Instance 2 (Different Broker/Strategy)
      ├── docker-compose.yaml
      └── .env
```

**Managing a Specific Instance:**
```bash
# Go to the instance directory
cd /opt/openalgo-algo1

# Start/Stop/Restart
docker compose up -d
docker compose stop
docker compose restart

# View Logs
docker compose logs -f
```

## Updating Existing Instances

When you run the script with existing domains, it will detect them and offer smart update options:

```
Instance for domain.com already exists. Update code only? (y=update, n=skip, r=reinstall):
```

| Option | Behavior |
|--------|----------|
| **y (Update)** | Pulls latest code, preserves `.env` file (passwords remain valid), skips all config prompts |
| **n (Skip)** | Skips this domain entirely |
| **r (Reinstall)** | Fresh install with new config (⚠️ regenerates security keys, invalidates existing passwords) |

### What Gets Preserved During Updates

When you choose **Update (y)**:
- ✅ `.env` file (APP_KEY, PEPPER, broker credentials)
- ✅ User passwords and login sessions
- ✅ SSL certificates
- ✅ Database (stored in Docker volumes)

### Portainer Smart Detection

If Portainer is already running, the script will:
1. Detect the existing installation
2. Offer to check for version updates
3. Skip redundant configuration prompts

## Troubleshooting

1.  **Healthcheck Failures**:
    - If the container shows `unhealthy`, ensure your `Dockerfile` includes `curl`. This script automatically patches standard Dockerfiles to include it.

2.  **SSL Errors**:
    - If using Custom SSL, ensure your `.pem` file supports the full chain and your `.key` file is unencrypted.
    - Check Nginx logs: `tail -f /var/log/nginx/error.log`

3.  **WebSocket 403 Errors**:
    - If you experience disconnects after broker re-login, restart the specific instance:
      ```bash
      cd /opt/openalgo-INSTANCE_NAME
      docker compose restart
      ```

```


---

# FILE: install\docker-run.bat

```bat
@echo off
REM ============================================================================
REM OpenAlgo Docker Runner for Windows
REM ============================================================================
REM
REM Quick Start (2 commands):
REM   1. Download: curl.exe -O https://raw.githubusercontent.com/marketcalls/openalgo/main/install/docker-run.bat
REM   2. Run:      docker-run.bat
REM
REM Commands:
REM   start    - Start OpenAlgo container (default, runs setup if needed)
REM   stop     - Stop and remove container
REM   restart  - Restart container
REM   logs     - View container logs (live)
REM   pull     - Pull latest image from Docker Hub
REM   status   - Show container status
REM   shell    - Open bash shell in container
REM   setup    - Re-run setup (regenerate keys, edit .env)
REM   help     - Show this help
REM
REM Prerequisites:
REM   - Docker Desktop installed and running
REM
REM ============================================================================

setlocal enabledelayedexpansion

REM Configuration
set IMAGE=marketcalls/openalgo:latest
set CONTAINER=openalgo
set ENV_FILE=.env
set SAMPLE_ENV_URL=https://raw.githubusercontent.com/marketcalls/openalgo/main/.sample.env
REM Use the directory where the script is located
set OPENALGO_DIR=%~dp0
REM Remove trailing backslash
if "%OPENALGO_DIR:~-1%"=="\" set OPENALGO_DIR=%OPENALGO_DIR:~0,-1%
set SETUP_FAILED=0

REM XTS Brokers that require market data credentials
set XTS_BROKERS=fivepaisaxts,compositedge,ibulls,iifl,jainamxts,rmoney,wisdom

REM Valid brokers list
set VALID_BROKERS=fivepaisa,fivepaisaxts,aliceblue,angel,compositedge,definedge,deltaexchange,dhan,dhan_sandbox,firstock,flattrade,fyers,groww,ibulls,iifl,iiflcapital,indmoney,jainamxts,kotak,motilal,mstock,nubra,paytm,pocketful,rmoney,samco,shoonya,tradejini,upstox,wisdom,zebu,zerodha

REM Banner
echo.
echo   ========================================
echo        OpenAlgo Docker Runner
echo        Windows Desktop Edition
echo   ========================================
echo.

REM Check if Docker is running
docker info >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker is not running!
    echo.
    echo Please start Docker Desktop first:
    echo   1. Open Docker Desktop from Start Menu
    echo   2. Wait for Docker to fully start
    echo   3. Run this script again
    echo.
    pause
    exit /b 1
)

REM Parse command
set CMD=%1
if "%CMD%"=="" set CMD=start

if /i "%CMD%"=="start" goto start
if /i "%CMD%"=="stop" goto stop
if /i "%CMD%"=="restart" goto restart
if /i "%CMD%"=="logs" goto logs
if /i "%CMD%"=="pull" goto pull
if /i "%CMD%"=="status" goto status
if /i "%CMD%"=="shell" goto shell
if /i "%CMD%"=="setup" goto setup
if /i "%CMD%"=="migrate" goto migrate
if /i "%CMD%"=="help" goto help
goto help

:setup
echo [INFO] Setting up OpenAlgo in %OPENALGO_DIR%...
echo.

REM Create db directory
if not exist "%OPENALGO_DIR%\db\" (
    echo [INFO] Creating database directory...
    md "%OPENALGO_DIR%\db" 2>nul
    if errorlevel 1 (
        echo [ERROR] Failed to create database directory
        set SETUP_FAILED=1
        goto setup_end
    )
)

REM Check if .env already exists
if exist "%OPENALGO_DIR%\%ENV_FILE%" (
    echo [WARNING] .env file already exists at %OPENALGO_DIR%\%ENV_FILE%
    set /p OVERWRITE="Do you want to overwrite it? (y/n): "
    if /i not "!OVERWRITE!"=="y" (
        echo [INFO] Setup cancelled. Using existing .env file.
        goto setup_end
    )
)

REM Download sample.env from GitHub using curl.exe (not PowerShell alias)
echo [INFO] Downloading configuration template from GitHub...

REM Try curl.exe first (Windows 10/11 has this)
where curl.exe >nul 2>&1
if errorlevel 1 (
    echo [INFO] curl.exe not found, trying PowerShell...
    powershell -Command "Invoke-WebRequest -Uri '%SAMPLE_ENV_URL%' -OutFile '%OPENALGO_DIR%\%ENV_FILE%'" 2>nul
) else (
    curl.exe -sL "%SAMPLE_ENV_URL%" -o "%OPENALGO_DIR%\%ENV_FILE%" 2>nul
)

REM Check if download succeeded
if not exist "%OPENALGO_DIR%\%ENV_FILE%" (
    echo [ERROR] Failed to download configuration template!
    echo Please check your internet connection.
    echo.
    echo Manual setup:
    echo   1. Download .sample.env from https://github.com/marketcalls/openalgo
    echo   2. Save it as %OPENALGO_DIR%\.env
    echo   3. Run this script again
    set SETUP_FAILED=1
    goto setup_end
)
echo [OK] Configuration template downloaded.

REM Generate random keys using Python
echo [INFO] Generating secure keys...
where python >nul 2>&1
if errorlevel 1 (
    echo [WARNING] Python not found. Keys will be generated using PowerShell.
    for /f %%i in ('powershell -Command "[guid]::NewGuid().ToString('N') + [guid]::NewGuid().ToString('N')"') do set APP_KEY=%%i
    for /f %%i in ('powershell -Command "[guid]::NewGuid().ToString('N') + [guid]::NewGuid().ToString('N')"') do set API_KEY_PEPPER=%%i
) else (
    for /f %%i in ('python -c "import secrets; print(secrets.token_hex(32))"') do set APP_KEY=%%i
    for /f %%i in ('python -c "import secrets; print(secrets.token_hex(32))"') do set API_KEY_PEPPER=%%i
)

REM Update .env file with generated keys
echo [INFO] Updating configuration with secure keys...
powershell -Command "(Get-Content '%OPENALGO_DIR%\%ENV_FILE%') -replace 'OPENALGO_PLACEHOLDER_APP_KEY_REGENERATE_BEFORE_USE', '%APP_KEY%' | Set-Content '%OPENALGO_DIR%\%ENV_FILE%'"
powershell -Command "(Get-Content '%OPENALGO_DIR%\%ENV_FILE%') -replace 'OPENALGO_PLACEHOLDER_API_KEY_PEPPER_REGENERATE_BEFORE_USE', '%API_KEY_PEPPER%' | Set-Content '%OPENALGO_DIR%\%ENV_FILE%'"
echo [OK] Secure keys generated and saved.

REM Get broker configuration
echo.
echo   ========================================
echo   Broker Configuration
echo   ========================================
echo.
echo   Valid brokers:
echo   fivepaisa, fivepaisaxts, aliceblue, angel, compositedge,
echo   definedge, deltaexchange, dhan, dhan_sandbox, firstock, flattrade, fyers,
echo   groww, ibulls, iifl, iiflcapital, indmoney, jainamxts, kotak, motilal,
echo   mstock, nubra, paytm, pocketful, rmoney, samco, shoonya,
echo   tradejini, upstox, wisdom, zebu, zerodha
echo.

:get_broker
set /p BROKER_NAME="Enter broker name (e.g., zerodha, fyers, angel): "

REM Validate broker name
echo,%VALID_BROKERS%, | findstr /i /c:",%BROKER_NAME%," >nul
if errorlevel 1 (
    echo [ERROR] Invalid broker: %BROKER_NAME%
    echo Please enter a valid broker name from the list above.
    goto get_broker
)

echo [OK] Broker: %BROKER_NAME%

REM Get broker API credentials
echo.
set /p BROKER_API_KEY="Enter your %BROKER_NAME% API Key: "
set /p BROKER_API_SECRET="Enter your %BROKER_NAME% API Secret: "

if "%BROKER_API_KEY%"=="" (
    echo [ERROR] API Key is required!
    set SETUP_FAILED=1
    goto setup_end
)

if "%BROKER_API_SECRET%"=="" (
    echo [ERROR] API Secret is required!
    set SETUP_FAILED=1
    goto setup_end
)

REM Check if XTS broker (requires market data credentials)
set IS_XTS=0
echo,%XTS_BROKERS%, | findstr /i /c:",%BROKER_NAME%," >nul
if not errorlevel 1 (
    set IS_XTS=1
    echo.
    echo [INFO] %BROKER_NAME% is an XTS-based broker.
    echo        Additional market data credentials are required.
    echo.
    set /p BROKER_API_KEY_MARKET="Enter Market Data API Key: "
    set /p BROKER_API_SECRET_MARKET="Enter Market Data API Secret: "

    if "!BROKER_API_KEY_MARKET!"=="" (
        echo [ERROR] Market Data API Key is required for XTS brokers!
        set SETUP_FAILED=1
        goto setup_end
    )
    if "!BROKER_API_SECRET_MARKET!"=="" (
        echo [ERROR] Market Data API Secret is required for XTS brokers!
        set SETUP_FAILED=1
        goto setup_end
    )
)

REM Update .env with broker configuration
echo.
echo [INFO] Updating broker configuration...

REM Update broker credentials
powershell -Command "(Get-Content '%OPENALGO_DIR%\%ENV_FILE%') -replace 'BROKER_API_KEY = ''YOUR_BROKER_API_KEY''', 'BROKER_API_KEY = ''%BROKER_API_KEY%''' | Set-Content '%OPENALGO_DIR%\%ENV_FILE%'"
powershell -Command "(Get-Content '%OPENALGO_DIR%\%ENV_FILE%') -replace 'BROKER_API_SECRET = ''YOUR_BROKER_API_SECRET''', 'BROKER_API_SECRET = ''%BROKER_API_SECRET%''' | Set-Content '%OPENALGO_DIR%\%ENV_FILE%'"

REM Update redirect URL with broker name (replace <broker> placeholder)
powershell -Command "(Get-Content '%OPENALGO_DIR%\%ENV_FILE%') -replace '<broker>', '%BROKER_NAME%' | Set-Content '%OPENALGO_DIR%\%ENV_FILE%'"

REM Update XTS market data credentials if applicable
if "%IS_XTS%"=="1" (
    powershell -Command "(Get-Content '%OPENALGO_DIR%\%ENV_FILE%') -replace 'BROKER_API_KEY_MARKET = ''YOUR_BROKER_MARKET_API_KEY''', 'BROKER_API_KEY_MARKET = ''!BROKER_API_KEY_MARKET!''' | Set-Content '%OPENALGO_DIR%\%ENV_FILE%'"
    powershell -Command "(Get-Content '%OPENALGO_DIR%\%ENV_FILE%') -replace 'BROKER_API_SECRET_MARKET = ''YOUR_BROKER_MARKET_API_SECRET''', 'BROKER_API_SECRET_MARKET = ''!BROKER_API_SECRET_MARKET!''' | Set-Content '%OPENALGO_DIR%\%ENV_FILE%'"
)

echo [OK] Broker configuration saved.
echo.
echo   ========================================
echo   Setup Complete!
echo   ========================================
echo.
echo   Broker:         %BROKER_NAME%
if "%IS_XTS%"=="1" (
    echo   Type:           XTS API [with market data]
)
echo   Data directory: %OPENALGO_DIR%
echo   Config file:    %OPENALGO_DIR%\%ENV_FILE%
echo   Database:       %OPENALGO_DIR%\db\
echo   Strategies:     %OPENALGO_DIR%\strategies\
echo   Logs:           %OPENALGO_DIR%\log\
echo.
echo   Redirect URL for broker portal:
echo   http://127.0.0.1:5000/%BROKER_NAME%/callback
echo.
echo   Documentation: https://docs.openalgo.in
echo.
set /p OPEN_ENV="Open .env in Notepad for review? (y/n): "
if /i "%OPEN_ENV%"=="y" (
    start notepad "%OPENALGO_DIR%\%ENV_FILE%"
)
echo.
echo [OK] Setup complete! Run 'docker-run.bat start' to launch OpenAlgo.

:setup_end
exit /b %SETUP_FAILED%

:start
echo [INFO] Starting OpenAlgo...
echo.

REM Check if setup is needed
if not exist "%OPENALGO_DIR%\%ENV_FILE%" (
    echo [INFO] First time setup detected. Running setup...
    echo.
    call :setup
    if errorlevel 1 (
        echo.
        echo [ERROR] Setup failed. Cannot start OpenAlgo.
        echo Please fix the issues above and try again.
        goto end
    )
    echo.
    echo [INFO] Starting OpenAlgo after setup...
    echo.
)

REM Create db, strategies, log, keys, and tmp directories if not exist
if not exist "%OPENALGO_DIR%\db\" (
    echo [INFO] Creating database directory...
    md "%OPENALGO_DIR%\db" 2>nul
)
if not exist "%OPENALGO_DIR%\strategies\" (
    echo [INFO] Creating strategies directory...
    md "%OPENALGO_DIR%\strategies" 2>nul
    md "%OPENALGO_DIR%\strategies\scripts" 2>nul
    md "%OPENALGO_DIR%\strategies\examples" 2>nul
)
if not exist "%OPENALGO_DIR%\log\" (
    echo [INFO] Creating log directory...
    md "%OPENALGO_DIR%\log" 2>nul
    md "%OPENALGO_DIR%\log\strategies" 2>nul
)
if not exist "%OPENALGO_DIR%\keys\" (
    echo [INFO] Creating keys directory...
    md "%OPENALGO_DIR%\keys" 2>nul
)
if not exist "%OPENALGO_DIR%\tmp\" (
    echo [INFO] Creating temp directory...
    md "%OPENALGO_DIR%\tmp" 2>nul
)

REM Pull latest image
echo [INFO] Pulling latest image...
docker pull %IMAGE%
if errorlevel 1 (
    echo [WARNING] Could not pull latest image. Using cached version if available.
)

REM Stop and remove existing container if exists
docker stop %CONTAINER% >nul 2>&1
docker rm %CONTAINER% >nul 2>&1

REM Calculate dynamic resource limits based on available RAM
for /f "tokens=2 delims==" %%i in ('wmic computersystem get TotalPhysicalMemory /value ^| findstr TotalPhysicalMemory') do set TOTAL_RAM_BYTES=%%i
set /a TOTAL_RAM_MB=%TOTAL_RAM_BYTES:~0,-6%

REM Get CPU cores
for /f "tokens=2 delims==" %%i in ('wmic cpu get NumberOfCores /value ^| findstr NumberOfCores') do set CPU_CORES=%%i
if "%CPU_CORES%"=="" set CPU_CORES=2

REM shm_size: 25% of RAM (min 256MB, max 2GB)
set /a SHM_SIZE_MB=%TOTAL_RAM_MB% / 4
if %SHM_SIZE_MB% LSS 256 set SHM_SIZE_MB=256
if %SHM_SIZE_MB% GTR 2048 set SHM_SIZE_MB=2048

REM Thread limits based on RAM (prevents RLIMIT_NPROC exhaustion)
REM Less than 3GB: 1 thread | 3-6GB: 2 threads | 6GB+: min(4, cores)
REM See: https://github.com/marketcalls/openalgo/issues/822
if %TOTAL_RAM_MB% LSS 3000 (
    set THREAD_LIMIT=1
) else if %TOTAL_RAM_MB% LSS 6000 (
    set THREAD_LIMIT=2
) else (
    if %CPU_CORES% LSS 4 (
        set THREAD_LIMIT=%CPU_CORES%
    ) else (
        set THREAD_LIMIT=4
    )
)

REM Strategy memory limit based on RAM
REM Less than 3GB: 256MB | 3-6GB: 512MB | 6GB+: 1024MB
if %TOTAL_RAM_MB% LSS 3000 (
    set STRATEGY_MEM_LIMIT=256
) else if %TOTAL_RAM_MB% LSS 6000 (
    set STRATEGY_MEM_LIMIT=512
) else (
    set STRATEGY_MEM_LIMIT=1024
)

echo [INFO] System: %TOTAL_RAM_MB%MB RAM, %CPU_CORES% cores
echo [INFO] Config: shm=%SHM_SIZE_MB%MB, threads=%THREAD_LIMIT%, strategy_mem=%STRATEGY_MEM_LIMIT%MB

REM Run container
echo [INFO] Starting container...
docker run -d ^
    --name %CONTAINER% ^
    --shm-size=%SHM_SIZE_MB%m ^
    -p 5000:5000 ^
    -p 8765:8765 ^
    -e "OPENBLAS_NUM_THREADS=%THREAD_LIMIT%" ^
    -e "OMP_NUM_THREADS=%THREAD_LIMIT%" ^
    -e "MKL_NUM_THREADS=%THREAD_LIMIT%" ^
    -e "NUMEXPR_NUM_THREADS=%THREAD_LIMIT%" ^
    -e "NUMBA_NUM_THREADS=%THREAD_LIMIT%" ^
    -e "STRATEGY_MEMORY_LIMIT_MB=%STRATEGY_MEM_LIMIT%" ^
    -e "TZ=Asia/Kolkata" ^
    -v "%OPENALGO_DIR%\db:/app/db" ^
    -v "%OPENALGO_DIR%\strategies:/app/strategies" ^
    -v "%OPENALGO_DIR%\log:/app/log" ^
    -v "%OPENALGO_DIR%\keys:/app/keys" ^
    -v "%OPENALGO_DIR%\tmp:/app/tmp" ^
    -v "%OPENALGO_DIR%\.env:/app/.env" ^
    --restart unless-stopped ^
    %IMAGE%

if errorlevel 1 (
    echo.
    echo [ERROR] Failed to start container!
    echo.
    echo Troubleshooting:
    echo   1. Check if ports 5000 and 8765 are available
    echo   2. Ensure Docker Desktop is running
    echo   3. Check .env file: %OPENALGO_DIR%\%ENV_FILE%
    echo.
    goto end
)

echo.
echo [SUCCESS] OpenAlgo started successfully!
echo.
echo   ========================================
echo   Web UI:     http://127.0.0.1:5000
echo   WebSocket:  ws://127.0.0.1:8765
echo   ========================================
echo.
echo   Data directory: %OPENALGO_DIR%
echo.
echo   Useful commands:
echo     docker-run.bat logs     - View logs
echo     docker-run.bat stop     - Stop OpenAlgo
echo     docker-run.bat restart  - Restart OpenAlgo
echo.
goto end

:stop
echo [INFO] Stopping OpenAlgo...
docker stop %CONTAINER% >nul 2>&1
docker rm %CONTAINER% >nul 2>&1
echo [OK] OpenAlgo stopped.
goto end

:restart
echo [INFO] Restarting OpenAlgo...
docker stop %CONTAINER% >nul 2>&1
docker rm %CONTAINER% >nul 2>&1
echo [OK] OpenAlgo stopped.
echo.
goto start

:logs
echo [INFO] Showing logs (Press Ctrl+C to exit)...
echo.
docker logs -f %CONTAINER%
goto end

:pull
echo [INFO] Pulling latest image...
docker pull %IMAGE%
if errorlevel 1 (
    echo [ERROR] Failed to pull image.
) else (
    echo [OK] Image updated successfully.
    echo [INFO] Run 'docker-run.bat restart' to apply the update.
)
goto end

:status
echo [INFO] Container status:
echo.
docker ps -a --filter "name=%CONTAINER%" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
echo.
REM Check if container is running
docker ps --filter "name=%CONTAINER%" --filter "status=running" | findstr %CONTAINER% >nul
if errorlevel 1 (
    echo [STATUS] OpenAlgo is NOT running.
) else (
    echo [STATUS] OpenAlgo is running.
    echo.
    echo   Web UI: http://127.0.0.1:5000
)
echo.
echo   Data directory: %OPENALGO_DIR%
goto end

:shell
echo [INFO] Opening shell in container...
docker exec -it %CONTAINER% /bin/bash
goto end

:migrate
echo [INFO] Running database migrations...
docker exec -it %CONTAINER% /app/.venv/bin/python /app/upgrade/migrate_all.py
if errorlevel 1 (
    echo [WARNING] Some migrations may have had issues. Check the output above.
) else (
    echo [OK] Migrations completed successfully.
)
goto end

:help
echo.
echo Usage: docker-run.bat [command]
echo.
echo Commands:
echo   start    Start OpenAlgo (runs setup if needed, default)
echo   stop     Stop and remove container
echo   restart  Restart container
echo   logs     View container logs (live)
echo   pull     Pull latest image from Docker Hub
echo   status   Show container status
echo   shell    Open bash shell in container
echo   migrate  Run database migrations manually
echo   setup    Re-run setup (regenerate keys, edit .env)
echo   help     Show this help
echo.
echo Quick Start:
echo   1. Install Docker Desktop: https://www.docker.com/products/docker-desktop
echo   2. Download this script (use PowerShell):
echo      curl.exe -O https://raw.githubusercontent.com/marketcalls/openalgo/main/install/docker-run.bat
echo   3. Run: docker-run.bat
echo.
echo Data Location: %OPENALGO_DIR%
echo   - Config:     %OPENALGO_DIR%\.env
echo   - Database:   %OPENALGO_DIR%\db\
echo   - Strategies: %OPENALGO_DIR%\strategies\
echo   - Logs:       %OPENALGO_DIR%\log\
echo.
echo XTS Brokers (require market data credentials):
echo   fivepaisaxts, compositedge, ibulls, iifl, jainamxts, rmoney, wisdom
echo.
goto end

:end
endlocal

```


---

# FILE: install\docker-run.sh

```sh
#!/bin/bash
# ============================================================================
# OpenAlgo Docker Runner for macOS/Linux
# ============================================================================
#
# Quick Start (2 commands):
#   1. Download: curl -O https://raw.githubusercontent.com/marketcalls/openalgo/main/install/docker-run.sh && chmod +x docker-run.sh
#   2. Run:      ./docker-run.sh
#
# Commands:
#   start    - Start OpenAlgo container (default, runs setup if needed)
#   stop     - Stop and remove container
#   restart  - Restart container
#   logs     - View container logs (live)
#   pull     - Pull latest image from Docker Hub
#   status   - Show container status
#   shell    - Open bash shell in container
#   migrate  - Run database migrations manually
#   setup    - Re-run setup (regenerate keys, edit .env)
#   help     - Show this help
#
# Prerequisites:
#   - Docker Desktop installed and running
#
# ============================================================================

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
IMAGE="marketcalls/openalgo:latest"
CONTAINER="openalgo"
ENV_FILE=".env"
SAMPLE_ENV_URL="https://raw.githubusercontent.com/marketcalls/openalgo/main/.sample.env"
# Use the directory where the script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OPENALGO_DIR="$SCRIPT_DIR"

# XTS Brokers that require market data credentials
XTS_BROKERS="fivepaisaxts,compositedge,ibulls,iifl,jainamxts,rmoney,wisdom"

# Valid brokers list
VALID_BROKERS="fivepaisa,fivepaisaxts,aliceblue,angel,compositedge,definedge,deltaexchange,dhan,dhan_sandbox,firstock,flattrade,fyers,groww,ibulls,iifl,iiflcapital,indmoney,jainamxts,kotak,motilal,mstock,nubra,paytm,pocketful,rmoney,samco,shoonya,tradejini,upstox,wisdom,zebu,zerodha"

# Banner
echo ""
echo -e "${BLUE}  ========================================${NC}"
echo -e "${BLUE}       OpenAlgo Docker Runner${NC}"
echo -e "${BLUE}       Desktop Edition (macOS/Linux)${NC}"
echo -e "${BLUE}  ========================================${NC}"
echo ""

# Function to print messages
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_ok() {
    echo -e "${GREEN}[OK]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

# Check if Docker is running
check_docker() {
    if ! docker info >/dev/null 2>&1; then
        log_error "Docker is not running!"
        echo ""
        echo "Please start Docker Desktop first:"
        if [[ "$OSTYPE" == "darwin"* ]]; then
            echo "  1. Open Docker Desktop from Applications"
        else
            echo "  1. Start Docker: sudo systemctl start docker"
            echo "     Or open Docker Desktop if using the desktop version"
        fi
        echo "  2. Wait for Docker to fully start"
        echo "  3. Run this script again"
        echo ""
        exit 1
    fi
}

# Validate broker name
validate_broker() {
    local broker=$1
    if [[ ",$VALID_BROKERS," == *",$broker,"* ]]; then
        return 0
    else
        return 1
    fi
}

# Check if broker is XTS based
is_xts_broker() {
    local broker=$1
    if [[ ",$XTS_BROKERS," == *",$broker,"* ]]; then
        return 0
    else
        return 1
    fi
}

# Setup function
do_setup() {
    log_info "Setting up OpenAlgo in $OPENALGO_DIR..."
    echo ""

    # Create db directory
    if [ ! -d "$OPENALGO_DIR/db" ]; then
        log_info "Creating database directory..."
        mkdir -p "$OPENALGO_DIR/db"
        if [ $? -ne 0 ]; then
            log_error "Failed to create database directory"
            return 1
        fi
    fi

    # Check if .env already exists
    if [ -f "$OPENALGO_DIR/$ENV_FILE" ]; then
        log_warn ".env file already exists at $OPENALGO_DIR/$ENV_FILE"
        read -p "Do you want to overwrite it? (y/n): " OVERWRITE
        if [[ ! "$OVERWRITE" =~ ^[Yy]$ ]]; then
            log_info "Setup cancelled. Using existing .env file."
            return 0
        fi
    fi

    # Download sample.env from GitHub
    log_info "Downloading configuration template from GitHub..."
    if ! curl -sL "$SAMPLE_ENV_URL" -o "$OPENALGO_DIR/$ENV_FILE"; then
        log_error "Failed to download configuration template!"
        echo "Please check your internet connection."
        return 1
    fi
    log_ok "Configuration template downloaded."

    # Generate random keys
    log_info "Generating secure keys..."

    # Check if Python is available
    if command -v python3 &> /dev/null; then
        PYTHON_CMD="python3"
    elif command -v python &> /dev/null; then
        PYTHON_CMD="python"
    else
        log_warn "Python not found. Using openssl for key generation."
        APP_KEY=$(openssl rand -hex 32)
        API_KEY_PEPPER=$(openssl rand -hex 32)
        if [ -z "$APP_KEY" ] || [ -z "$API_KEY_PEPPER" ]; then
            log_error "Failed to generate keys. Please install Python or openssl."
            return 1
        fi
    fi

    if [ -z "$APP_KEY" ]; then
        APP_KEY=$($PYTHON_CMD -c "import secrets; print(secrets.token_hex(32))")
        API_KEY_PEPPER=$($PYTHON_CMD -c "import secrets; print(secrets.token_hex(32))")
    fi

    # Update .env file with generated keys
    log_info "Updating configuration with secure keys..."
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS sed syntax
        sed -i '' "s/OPENALGO_PLACEHOLDER_APP_KEY_REGENERATE_BEFORE_USE/$APP_KEY/g" "$OPENALGO_DIR/$ENV_FILE"
        sed -i '' "s/OPENALGO_PLACEHOLDER_API_KEY_PEPPER_REGENERATE_BEFORE_USE/$API_KEY_PEPPER/g" "$OPENALGO_DIR/$ENV_FILE"
    else
        # Linux sed syntax
        sed -i "s/OPENALGO_PLACEHOLDER_APP_KEY_REGENERATE_BEFORE_USE/$APP_KEY/g" "$OPENALGO_DIR/$ENV_FILE"
        sed -i "s/OPENALGO_PLACEHOLDER_API_KEY_PEPPER_REGENERATE_BEFORE_USE/$API_KEY_PEPPER/g" "$OPENALGO_DIR/$ENV_FILE"
    fi
    # .env is now bind-mounted read+write into the container so auto-rotation
    # of compromised APP_KEY/API_KEY_PEPPER (utils/env_check.py) can run.
    # Container runs as appuser (UID 1000); chown UID 1000 + chmod 600 gives
    # appuser read+write while keeping the file private on the host.
    # On Linux this needs sudo if the script wasn't run as root; on macOS
    # Docker Desktop handles UID mapping in its VM so chown is a no-op.
    if [ "$(uname)" = "Linux" ]; then
        if [ "$EUID" -ne 0 ] && command -v sudo >/dev/null 2>&1; then
            sudo chown 1000:1000 "$OPENALGO_DIR/$ENV_FILE" 2>/dev/null || true
            sudo chmod 600 "$OPENALGO_DIR/$ENV_FILE" 2>/dev/null || true
        else
            chown 1000:1000 "$OPENALGO_DIR/$ENV_FILE" 2>/dev/null || true
            chmod 600 "$OPENALGO_DIR/$ENV_FILE" 2>/dev/null || true
        fi
    else
        chmod 600 "$OPENALGO_DIR/$ENV_FILE" 2>/dev/null || true
    fi
    log_ok "Secure keys generated and saved."

    # Get broker configuration
    echo ""
    echo -e "${BLUE}  ========================================${NC}"
    echo -e "${BLUE}  Broker Configuration${NC}"
    echo -e "${BLUE}  ========================================${NC}"
    echo ""
    echo "  Valid brokers:"
    echo "  fivepaisa, fivepaisaxts, aliceblue, angel, compositedge,"
    echo "  definedge, deltaexchange, dhan, dhan_sandbox, firstock, flattrade, fyers,"
    echo "  groww, ibulls, iifl, iiflcapital, indmoney, jainamxts, kotak, motilal,"
    echo "  mstock, nubra, paytm, pocketful, rmoney, samco, shoonya,"
    echo "  tradejini, upstox, wisdom, zebu, zerodha"
    echo ""

    # Get broker name with validation
    while true; do
        read -p "Enter broker name (e.g., zerodha, fyers, angel): " BROKER_NAME
        if validate_broker "$BROKER_NAME"; then
            break
        else
            log_error "Invalid broker: $BROKER_NAME"
            echo "Please enter a valid broker name from the list above."
        fi
    done
    log_ok "Broker: $BROKER_NAME"

    # Get broker API credentials
    echo ""
    read -p "Enter your $BROKER_NAME API Key: " BROKER_API_KEY
    read -p "Enter your $BROKER_NAME API Secret: " BROKER_API_SECRET

    if [ -z "$BROKER_API_KEY" ]; then
        log_error "API Key is required!"
        return 1
    fi

    if [ -z "$BROKER_API_SECRET" ]; then
        log_error "API Secret is required!"
        return 1
    fi

    # Check if XTS broker (requires market data credentials)
    IS_XTS=0
    if is_xts_broker "$BROKER_NAME"; then
        IS_XTS=1
        echo ""
        log_info "$BROKER_NAME is an XTS-based broker."
        echo "       Additional market data credentials are required."
        echo ""
        read -p "Enter Market Data API Key: " BROKER_API_KEY_MARKET
        read -p "Enter Market Data API Secret: " BROKER_API_SECRET_MARKET

        if [ -z "$BROKER_API_KEY_MARKET" ]; then
            log_error "Market Data API Key is required for XTS brokers!"
            return 1
        fi
        if [ -z "$BROKER_API_SECRET_MARKET" ]; then
            log_error "Market Data API Secret is required for XTS brokers!"
            return 1
        fi
    fi

    # Update .env with broker configuration
    echo ""
    log_info "Updating broker configuration..."

    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS sed syntax
        sed -i '' "s/BROKER_API_KEY = 'YOUR_BROKER_API_KEY'/BROKER_API_KEY = '$BROKER_API_KEY'/g" "$OPENALGO_DIR/$ENV_FILE"
        sed -i '' "s/BROKER_API_SECRET = 'YOUR_BROKER_API_SECRET'/BROKER_API_SECRET = '$BROKER_API_SECRET'/g" "$OPENALGO_DIR/$ENV_FILE"
        sed -i '' "s|<broker>|$BROKER_NAME|g" "$OPENALGO_DIR/$ENV_FILE"

        if [ "$IS_XTS" -eq 1 ]; then
            sed -i '' "s/BROKER_API_KEY_MARKET = 'YOUR_BROKER_MARKET_API_KEY'/BROKER_API_KEY_MARKET = '$BROKER_API_KEY_MARKET'/g" "$OPENALGO_DIR/$ENV_FILE"
            sed -i '' "s/BROKER_API_SECRET_MARKET = 'YOUR_BROKER_MARKET_API_SECRET'/BROKER_API_SECRET_MARKET = '$BROKER_API_SECRET_MARKET'/g" "$OPENALGO_DIR/$ENV_FILE"
        fi
    else
        # Linux sed syntax
        sed -i "s/BROKER_API_KEY = 'YOUR_BROKER_API_KEY'/BROKER_API_KEY = '$BROKER_API_KEY'/g" "$OPENALGO_DIR/$ENV_FILE"
        sed -i "s/BROKER_API_SECRET = 'YOUR_BROKER_API_SECRET'/BROKER_API_SECRET = '$BROKER_API_SECRET'/g" "$OPENALGO_DIR/$ENV_FILE"
        sed -i "s|<broker>|$BROKER_NAME|g" "$OPENALGO_DIR/$ENV_FILE"

        if [ "$IS_XTS" -eq 1 ]; then
            sed -i "s/BROKER_API_KEY_MARKET = 'YOUR_BROKER_MARKET_API_KEY'/BROKER_API_KEY_MARKET = '$BROKER_API_KEY_MARKET'/g" "$OPENALGO_DIR/$ENV_FILE"
            sed -i "s/BROKER_API_SECRET_MARKET = 'YOUR_BROKER_MARKET_API_SECRET'/BROKER_API_SECRET_MARKET = '$BROKER_API_SECRET_MARKET'/g" "$OPENALGO_DIR/$ENV_FILE"
        fi
    fi

    log_ok "Broker configuration saved."

    echo ""
    echo -e "${GREEN}  ========================================${NC}"
    echo -e "${GREEN}  Setup Complete!${NC}"
    echo -e "${GREEN}  ========================================${NC}"
    echo ""
    echo "  Broker:         $BROKER_NAME"
    if [ "$IS_XTS" -eq 1 ]; then
        echo "  Type:           XTS API (with market data)"
    fi
    echo "  Data directory: $OPENALGO_DIR"
    echo "  Config file:    $OPENALGO_DIR/$ENV_FILE"
    echo "  Database:       $OPENALGO_DIR/db/"
    echo "  Strategies:     $OPENALGO_DIR/strategies/"
    echo "  Logs:           $OPENALGO_DIR/log/"
    echo ""
    echo "  Redirect URL for broker portal:"
    echo "  http://127.0.0.1:5000/$BROKER_NAME/callback"
    echo ""
    echo "  Documentation: https://docs.openalgo.in"
    echo ""

    # Try to open .env in editor (non-blocking)
    read -p "Open .env in editor for review? (y/n): " OPEN_EDITOR
    if [[ "$OPEN_EDITOR" =~ ^[Yy]$ ]]; then
        if [[ "$OSTYPE" == "darwin"* ]]; then
            open -t "$OPENALGO_DIR/$ENV_FILE"
        elif command -v xdg-open &> /dev/null; then
            # Linux with desktop environment - non-blocking
            xdg-open "$OPENALGO_DIR/$ENV_FILE" &>/dev/null &
        elif command -v gedit &> /dev/null; then
            gedit "$OPENALGO_DIR/$ENV_FILE" &>/dev/null &
        elif command -v code &> /dev/null; then
            code "$OPENALGO_DIR/$ENV_FILE"
        else
            echo "  Edit .env manually: $OPENALGO_DIR/$ENV_FILE"
        fi
    fi

    echo ""
    log_ok "Setup complete! Run './docker-run.sh start' to launch OpenAlgo."
    echo ""
    return 0
}

# Start function
do_start() {
    log_info "Starting OpenAlgo..."
    echo ""

    # Check if setup is needed
    if [ ! -f "$OPENALGO_DIR/$ENV_FILE" ]; then
        log_info "First time setup detected. Running setup..."
        echo ""
        if ! do_setup; then
            echo ""
            log_error "Setup failed. Cannot start OpenAlgo."
            echo "Please fix the issues above and try again."
            exit 1
        fi
        echo ""
        log_info "Starting OpenAlgo after setup..."
        echo ""
    fi

    # Create db, strategies, log, keys, and tmp directories if not exist
    if [ ! -d "$OPENALGO_DIR/db" ]; then
        log_info "Creating database directory..."
        mkdir -p "$OPENALGO_DIR/db"
    fi
    if [ ! -d "$OPENALGO_DIR/strategies" ]; then
        log_info "Creating strategies directory..."
        mkdir -p "$OPENALGO_DIR/strategies/scripts"
        mkdir -p "$OPENALGO_DIR/strategies/examples"
    fi
    if [ ! -d "$OPENALGO_DIR/log" ]; then
        log_info "Creating log directory..."
        mkdir -p "$OPENALGO_DIR/log/strategies"
    fi
    if [ ! -d "$OPENALGO_DIR/keys" ]; then
        log_info "Creating keys directory..."
        mkdir -p "$OPENALGO_DIR/keys"
    fi
    if [ ! -d "$OPENALGO_DIR/tmp" ]; then
        log_info "Creating temp directory..."
        mkdir -p "$OPENALGO_DIR/tmp"
    fi

    # Pull latest image
    log_info "Pulling latest image..."
    if ! docker pull "$IMAGE"; then
        log_warn "Could not pull latest image. Using cached version if available."
    fi

    # Stop and remove existing container if exists
    docker stop "$CONTAINER" >/dev/null 2>&1
    docker rm "$CONTAINER" >/dev/null 2>&1

    # Calculate dynamic resource limits based on available RAM
    if [[ "$OSTYPE" == "darwin"* ]]; then
        TOTAL_RAM_MB=$(($(sysctl -n hw.memsize) / 1024 / 1024))
        CPU_CORES=$(sysctl -n hw.ncpu 2>/dev/null || echo 2)
    else
        TOTAL_RAM_MB=$(($(grep MemTotal /proc/meminfo | awk '{print $2}') / 1024))
        CPU_CORES=$(nproc 2>/dev/null || echo 2)
    fi

    # shm_size: 25% of RAM (min 256MB, max 2GB)
    SHM_SIZE_MB=$((TOTAL_RAM_MB / 4))
    [ $SHM_SIZE_MB -lt 256 ] && SHM_SIZE_MB=256
    [ $SHM_SIZE_MB -gt 2048 ] && SHM_SIZE_MB=2048

    # Thread limits based on RAM (prevents RLIMIT_NPROC exhaustion)
    # <3GB: 1 thread | 3-6GB: 2 threads | 6GB+: min(4, cores)
    # See: https://github.com/marketcalls/openalgo/issues/822
    if [ $TOTAL_RAM_MB -lt 3000 ]; then
        THREAD_LIMIT=1
    elif [ $TOTAL_RAM_MB -lt 6000 ]; then
        THREAD_LIMIT=2
    else
        THREAD_LIMIT=$((CPU_CORES < 4 ? CPU_CORES : 4))
    fi

    # Strategy memory limit based on RAM
    # <3GB: 256MB | 3-6GB: 512MB | 6GB+: 1024MB
    if [ $TOTAL_RAM_MB -lt 3000 ]; then
        STRATEGY_MEM_LIMIT=256
    elif [ $TOTAL_RAM_MB -lt 6000 ]; then
        STRATEGY_MEM_LIMIT=512
    else
        STRATEGY_MEM_LIMIT=1024
    fi

    log_info "System: ${TOTAL_RAM_MB}MB RAM, ${CPU_CORES} cores"
    log_info "Config: shm=${SHM_SIZE_MB}MB, threads=${THREAD_LIMIT}, strategy_mem=${STRATEGY_MEM_LIMIT}MB"

    # Run container
    log_info "Starting container..."
    if docker run -d \
        --name "$CONTAINER" \
        --shm-size=${SHM_SIZE_MB}m \
        -p 5000:5000 \
        -p 8765:8765 \
        -e "OPENBLAS_NUM_THREADS=${THREAD_LIMIT}" \
        -e "OMP_NUM_THREADS=${THREAD_LIMIT}" \
        -e "MKL_NUM_THREADS=${THREAD_LIMIT}" \
        -e "NUMEXPR_NUM_THREADS=${THREAD_LIMIT}" \
        -e "NUMBA_NUM_THREADS=${THREAD_LIMIT}" \
        -e "STRATEGY_MEMORY_LIMIT_MB=${STRATEGY_MEM_LIMIT}" \
        -e "TZ=Asia/Kolkata" \
        -v "$OPENALGO_DIR/db:/app/db" \
        -v "$OPENALGO_DIR/strategies:/app/strategies" \
        -v "$OPENALGO_DIR/log:/app/log" \
        -v "$OPENALGO_DIR/keys:/app/keys" \
        -v "$OPENALGO_DIR/tmp:/app/tmp" \
        -v "$OPENALGO_DIR/.env:/app/.env" \
        --restart unless-stopped \
        "$IMAGE"; then

        echo ""
        log_success "OpenAlgo started successfully!"
        echo ""
        echo -e "${GREEN}  ========================================${NC}"
        echo -e "${GREEN}  Web UI:     http://127.0.0.1:5000${NC}"
        echo -e "${GREEN}  WebSocket:  ws://127.0.0.1:8765${NC}"
        echo -e "${GREEN}  ========================================${NC}"
        echo ""
        echo "  Data directory: $OPENALGO_DIR"
        echo ""
        echo "  Useful commands:"
        echo "    ./docker-run.sh logs     - View logs"
        echo "    ./docker-run.sh stop     - Stop OpenAlgo"
        echo "    ./docker-run.sh restart  - Restart OpenAlgo"
        echo ""
    else
        echo ""
        log_error "Failed to start container!"
        echo ""
        echo "Troubleshooting:"
        echo "  1. Check if ports 5000 and 8765 are available"
        echo "  2. Ensure Docker Desktop is running"
        echo "  3. Check .env file: $OPENALGO_DIR/$ENV_FILE"
        echo ""
        exit 1
    fi
}

# Stop function
do_stop() {
    log_info "Stopping OpenAlgo..."
    docker stop "$CONTAINER" >/dev/null 2>&1
    docker rm "$CONTAINER" >/dev/null 2>&1
    log_ok "OpenAlgo stopped."
}

# Restart function
do_restart() {
    log_info "Restarting OpenAlgo..."
    do_stop
    echo ""
    do_start
}

# Logs function
do_logs() {
    log_info "Showing logs (Press Ctrl+C to exit)..."
    echo ""
    docker logs -f "$CONTAINER"
}

# Pull function
do_pull() {
    log_info "Pulling latest image..."
    if docker pull "$IMAGE"; then
        log_ok "Image updated successfully."
        log_info "Run './docker-run.sh restart' to apply the update."
    else
        log_error "Failed to pull image."
        exit 1
    fi
}

# Status function
do_status() {
    log_info "Container status:"
    echo ""
    docker ps -a --filter "name=$CONTAINER" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
    echo ""

    # Check if container is running
    if docker ps --filter "name=$CONTAINER" --filter "status=running" | grep -q "$CONTAINER"; then
        echo -e "${GREEN}[STATUS]${NC} OpenAlgo is running."
        echo ""
        echo "  Web UI: http://127.0.0.1:5000"
    else
        echo -e "${YELLOW}[STATUS]${NC} OpenAlgo is NOT running."
    fi
    echo ""
    echo "  Data directory: $OPENALGO_DIR"
}

# Shell function
do_shell() {
    log_info "Opening shell in container..."
    docker exec -it "$CONTAINER" /bin/bash
}

# Migrate function
do_migrate() {
    log_info "Running database migrations..."
    docker exec -it "$CONTAINER" /app/.venv/bin/python /app/upgrade/migrate_all.py
    if [ $? -eq 0 ]; then
        log_ok "Migrations completed successfully."
    else
        log_warn "Some migrations may have had issues. Check the output above."
    fi
}

# Help function
do_help() {
    echo ""
    echo "Usage: ./docker-run.sh [command]"
    echo ""
    echo "Commands:"
    echo "  start    Start OpenAlgo (runs setup if needed, default)"
    echo "  stop     Stop and remove container"
    echo "  restart  Restart container"
    echo "  logs     View container logs (live)"
    echo "  pull     Pull latest image from Docker Hub"
    echo "  status   Show container status"
    echo "  shell    Open bash shell in container"
    echo "  migrate  Run database migrations manually"
    echo "  setup    Re-run setup (regenerate keys, edit .env)"
    echo "  help     Show this help"
    echo ""
    echo "Quick Start:"
    echo "  1. Install Docker Desktop:"
    echo "     macOS: https://docs.docker.com/desktop/install/mac-install/"
    echo "     Linux: https://docs.docker.com/desktop/install/linux-install/"
    echo ""
    echo "  2. Download and run:"
    echo "     curl -O https://raw.githubusercontent.com/marketcalls/openalgo/main/install/docker-run.sh"
    echo "     chmod +x docker-run.sh"
    echo "     ./docker-run.sh"
    echo ""
    echo "Data Location: $OPENALGO_DIR"
    echo "  - Config:     $OPENALGO_DIR/.env"
    echo "  - Database:   $OPENALGO_DIR/db/"
    echo "  - Strategies: $OPENALGO_DIR/strategies/"
    echo "  - Logs:       $OPENALGO_DIR/log/"
    echo ""
    echo "XTS Brokers (require market data credentials):"
    echo "  fivepaisaxts, compositedge, ibulls, iifl, jainamxts, rmoney, wisdom"
    echo ""
}

# Check Docker is running (except for help)
CMD="${1:-start}"
if [[ "$CMD" != "help" && "$CMD" != "--help" && "$CMD" != "-h" ]]; then
    check_docker
fi

# Parse command
case "$CMD" in
    start)
        do_start
        ;;
    stop)
        do_stop
        ;;
    restart)
        do_restart
        ;;
    logs)
        do_logs
        ;;
    pull)
        do_pull
        ;;
    status)
        do_status
        ;;
    shell)
        do_shell
        ;;
    migrate)
        do_migrate
        ;;
    setup)
        do_setup
        ;;
    help|--help|-h)
        do_help
        ;;
    *)
        log_error "Unknown command: $CMD"
        do_help
        exit 1
        ;;
esac

```


---

# FILE: install\enable-remote-mcp-docker.sh

```sh
#!/bin/bash
# ============================================================================
# OpenAlgo Remote MCP enabler — Docker variant
# ============================================================================
# Run AFTER a successful install via install-docker.sh or
# install-docker-multi-custom-ssl.sh. Detects Docker Compose stacks
# under /opt/openalgo/<domain>/ (or a path you provide), edits the
# bind-mounted .env, restarts the container.
#
# Database migrations:
#   The Docker container's start.sh ALREADY runs migrate_all.py on
#   every container start, so you don't need to run them separately
#   here — restarting the container picks them up. This is the one
#   advantage Docker has over the native install path on upgrades.
#
# What this script does:
#   1. Detect Docker Compose stacks under /opt/openalgo (default)
#   2. Pick one (or run for all in batch mode)
#   3. Backs up the per-instance .env
#   4. Adds / updates MCP_* keys in .env
#   5. docker compose restart for the picked instance
#   6. Smoke-probes the OAuth + MCP endpoints over the public domain
#
# Defaults:
#   * MCP_OAUTH_REQUIRE_APPROVAL = True
#   * MCP_OAUTH_WRITE_SCOPE_ENABLED = False
#   * MCP_HTTP_CORS_ORIGINS = "https://claude.ai,https://chatgpt.com"
# Edit the .env afterwards to flip these if your deployment requires.
# ============================================================================

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() { printf '%b\n' "${2:-$NC}$1$NC"; }
fail() { log "$1" "$RED"; exit 1; }


# ---------------------------------------------------------------------------
# 0. Sanity
# ---------------------------------------------------------------------------
if [[ $EUID -ne 0 ]]; then
    fail "Please run this script with sudo."
fi

if ! command -v docker >/dev/null 2>&1; then
    fail "docker is not installed. This script targets Docker installs only."
fi

if ! docker compose version >/dev/null 2>&1; then
    fail "'docker compose' (v2 plugin) is not available. Update your Docker Engine."
fi


# ---------------------------------------------------------------------------
# 1. Discover Docker Compose stacks
# ---------------------------------------------------------------------------
INSTALL_BASE="${INSTALL_BASE:-/opt/openalgo}"

log "\n[1/5] Detecting OpenAlgo Docker stacks..." "$BLUE"
log "Looking under: $INSTALL_BASE" "$YELLOW"

mapfile -t STACK_DIRS < <(find "$INSTALL_BASE" -maxdepth 2 -name "docker-compose.yaml" -o -name "docker-compose.yml" 2>/dev/null \
    | xargs -I {} dirname {} | sort -u)

if [[ ${#STACK_DIRS[@]} -eq 0 ]]; then
    fail "No docker-compose.{yaml,yml} files found under $INSTALL_BASE.
Either you installed elsewhere — re-run with INSTALL_BASE=/your/path
in front of the script — or you haven't run install-docker.sh /
install-docker-multi-custom-ssl.sh yet."
fi

# Pick a single stack; multi-instance setups can re-run this script
# for each one. (A future enhancement could batch-enable all of them.)
if [[ ${#STACK_DIRS[@]} -gt 1 ]]; then
    log "Multiple Docker stacks detected:" "$YELLOW"
    for i in "${!STACK_DIRS[@]}"; do
        printf '  [%d] %s\n' "$((i+1))" "${STACK_DIRS[$i]}"
    done
    read -rp "Pick one [1-${#STACK_DIRS[@]}]: " PICK
    # Validate: must be a positive integer in range. Empty or non-numeric
    # input would otherwise resolve to ${STACK_DIRS[-1]} (last element)
    # silently selecting the wrong deployment.
    if ! [[ "$PICK" =~ ^[1-9][0-9]*$ ]] || (( PICK > ${#STACK_DIRS[@]} )); then
        fail "Invalid selection: $PICK. Must be 1..${#STACK_DIRS[@]}."
    fi
    STACK_DIR="${STACK_DIRS[$((PICK-1))]}"
else
    STACK_DIR="${STACK_DIRS[0]}"
fi
[[ -d "$STACK_DIR" ]] || fail "Picked stack directory does not exist: $STACK_DIR"
log "Stack: $STACK_DIR" "$GREEN"

# Each install-docker* script bind-mounts .env from the stack
# directory into /app/.env in the container.
ENV_FILE="$STACK_DIR/.env"
[[ -f "$ENV_FILE" ]] || fail "No .env at $ENV_FILE — install scripts should have created one."


# ---------------------------------------------------------------------------
# 2. Pre-flight: refuse if FLASK_DEBUG=True
# ---------------------------------------------------------------------------
if grep -qE "^[[:space:]]*FLASK_DEBUG[[:space:]]*=[[:space:]]*['\"]?[Tt]rue" "$ENV_FILE"; then
    log "\nFLASK_DEBUG=True is set in $ENV_FILE." "$RED"
    log "Remote MCP refuses to start in debug mode (token leak risk via" "$RED"
    log "Werkzeug tracebacks). Set FLASK_DEBUG=False, then retry." "$RED"
    exit 1
fi


# ---------------------------------------------------------------------------
# 3. Determine the public URL
# ---------------------------------------------------------------------------
log "\n[2/5] Public MCP URL" "$BLUE"

# install-docker-multi-custom-ssl.sh names the stack directory after
# the domain (/opt/openalgo/<domain>/), so derive the suggested
# public URL from the path. Fall back to HOST_SERVER in .env when the
# layout differs.
GUESSED_DOMAIN=$(basename "$STACK_DIR")
if [[ "$GUESSED_DOMAIN" =~ \. ]]; then
    DEFAULT_URL="https://$GUESSED_DOMAIN"
else
    DEFAULT_URL=""
fi

if [[ -z "$DEFAULT_URL" ]]; then
    DEFAULT_URL=$(grep -E "^[[:space:]]*HOST_SERVER[[:space:]]*=" "$ENV_FILE" \
        | head -n1 | sed -E "s/.*=[[:space:]]*['\"]?([^'\"]+)['\"]?.*/\1/")
fi

log "Same-domain mode: hosted MCP clients reach the server via the same" "$YELLOW"
log "  hostname as the dashboard. The existing nginx config that fronts" "$YELLOW"
log "  this Docker container already proxies /mcp, /oauth, and" "$YELLOW"
log "  /.well-known/oauth-* — no extra config required." "$YELLOW"
read -rp "Public MCP URL [$DEFAULT_URL]: " MCP_URL
MCP_URL="${MCP_URL:-$DEFAULT_URL}"
MCP_URL="${MCP_URL%/}"

if [[ ! "$MCP_URL" =~ ^https://[A-Za-z0-9.\-]+(/.*)?$ ]]; then
    fail "MCP URL must be HTTPS. Got: $MCP_URL"
fi
log "MCP_PUBLIC_URL = $MCP_URL" "$GREEN"


# ---------------------------------------------------------------------------
# 4. Confirm security defaults
# ---------------------------------------------------------------------------
log "\n[3/5] Security defaults" "$BLUE"
log "  MCP_OAUTH_REQUIRE_APPROVAL = True  (DCR clients require admin approval)" "$YELLOW"
log "  MCP_OAUTH_WRITE_SCOPE_ENABLED = False (read-only — no order placement via MCP)" "$YELLOW"
log "" "$NC"
log "Edit $ENV_FILE manually to flip these later. To enable order" "$YELLOW"
log "placement: set MCP_OAUTH_WRITE_SCOPE_ENABLED='True' and re-restart" "$YELLOW"
log "the container. Re-authorize the MCP client afterwards." "$YELLOW"
read -rp "Continue with defaults? [Y/n]: " GO
case "${GO,,}" in
    n|no) fail "Aborted." ;;
esac


# ---------------------------------------------------------------------------
# 5. Update the .env
# ---------------------------------------------------------------------------
log "\n[4/5] Updating $ENV_FILE..." "$BLUE"

set_env() {
    local key="$1"
    local value="$2"
    if grep -qE "^[[:space:]]*${key}[[:space:]]*=" "$ENV_FILE"; then
        sed -i "s|^[[:space:]]*${key}[[:space:]]*=.*|${key} = '${value}'|" "$ENV_FILE"
    else
        echo "${key} = '${value}'" >> "$ENV_FILE"
    fi
}

BACKUP="${ENV_FILE}.pre-mcp.$(date +%Y%m%d-%H%M%S)"
cp -p "$ENV_FILE" "$BACKUP"
log "Backup written to $BACKUP" "$GREEN"

set_env "MCP_HTTP_ENABLED" "True"
set_env "MCP_PUBLIC_URL" "$MCP_URL"
set_env "MCP_OAUTH_REQUIRE_APPROVAL" "True"
set_env "MCP_OAUTH_WRITE_SCOPE_ENABLED" "False"
# Default CORS allowlist for the two main hosted clients. Edit if you
# only need one or want to add more (mobile etc.).
if ! grep -qE "^[[:space:]]*MCP_HTTP_CORS_ORIGINS[[:space:]]*=" "$ENV_FILE"; then
    set_env "MCP_HTTP_CORS_ORIGINS" "https://claude.ai,https://chatgpt.com"
fi

# Match the bind-mount's expected ownership (Docker container runs as
# UID 1000). install-docker-multi-custom-ssl.sh already chown 1000
# the .env after fresh creation — preserving that on update.
chown 1000:1000 "$ENV_FILE" 2>/dev/null || true
chmod 600 "$ENV_FILE"
log ".env updated" "$GREEN"


# ---------------------------------------------------------------------------
# 6. Restart container
# ---------------------------------------------------------------------------
log "\n[5/5] Restarting Docker stack..." "$BLUE"
# The container's start.sh runs migrate_all.py before gunicorn — schema
# changes (2FA flag columns) apply automatically on this restart.
( cd "$STACK_DIR" && docker compose restart ) \
    || fail "docker compose restart failed. Check: cd $STACK_DIR && docker compose logs --tail=80"

# Give Gunicorn a moment to come up before probing.
sleep 4

# Confirm the container is healthy.
HEALTH=$(cd "$STACK_DIR" && docker compose ps --format json 2>/dev/null \
    | grep -oE '"State":"[^"]+"' | head -n1 || true)
if [[ -z "$HEALTH" ]] || [[ "$HEALTH" != *"running"* ]]; then
    log "Container did not return to running state after restart." "$RED"
    log "Inspect: cd $STACK_DIR && docker compose logs --tail=80" "$RED"
    log "Roll back .env with: cp '$BACKUP' '$ENV_FILE' && cd $STACK_DIR && docker compose restart" "$YELLOW"
    exit 1
fi


# ---------------------------------------------------------------------------
# Smoke checks
# ---------------------------------------------------------------------------
log "\nVerifying endpoints..." "$BLUE"
sleep 1

PROBE_FAILURES=0

probe() {
    local label="$1"
    local url="$2"
    local code
    # Drop -k so an invalid TLS cert is reported as a smoke-probe failure
    # rather than a silent pass. The whole point of probing the public
    # URL is to validate that the deployment is reachable from outside.
    code=$(curl -sS -o /dev/null -w '%{http_code}' --max-time 5 "$url" 2>/dev/null || echo "000")
    if [[ "$code" =~ ^(200|401|403)$ ]]; then
        log "  ✓ ${label}  → ${code}" "$GREEN"
    else
        log "  ✗ ${label}  → ${code}" "$RED"
        PROBE_FAILURES=$((PROBE_FAILURES + 1))
    fi
}

probe "OAuth discovery" "$MCP_URL/.well-known/oauth-authorization-server"
probe "Resource metadata" "$MCP_URL/.well-known/oauth-protected-resource"
probe "JWKS"             "$MCP_URL/oauth/jwks.json"
probe "MCP healthz"      "$MCP_URL/mcp/healthz"
probe "MCP (no token)"   "$MCP_URL/mcp"  # expect 401


# ---------------------------------------------------------------------------
# Closing message
# ---------------------------------------------------------------------------
if (( PROBE_FAILURES > 0 )); then
    log "" "$NC"
    log "$PROBE_FAILURES smoke probe(s) failed. Common causes:" "$RED"
    log "  - DNS for $MCP_URL not yet resolving (or wrong hostname)" "$RED"
    log "  - HTTPS certificate not yet issued / not trusted from this host" "$RED"
    log "  - Reverse proxy not yet routing /mcp + /oauth/* + /.well-known/*" "$RED"
    log "  - Container still booting; retry in a few seconds" "$RED"
    log "Roll back .env with: cp '$BACKUP' '$ENV_FILE' && cd $STACK_DIR && docker compose restart" "$YELLOW"
    exit 1
fi

cat <<EOF

$(printf '%b' "${GREEN}=========================================================${NC}")
$(printf '%b' "${GREEN} Remote MCP enabled successfully (Docker)${NC}")
$(printf '%b' "${GREEN}=========================================================${NC}")

  Public URL: $MCP_URL/mcp
  Discovery : $MCP_URL/.well-known/oauth-authorization-server
  Audit log : ${STACK_DIR}/log/mcp.jsonl  (Docker volume — see docker compose logs)
  Stack     : $STACK_DIR

  Next steps for connecting from a hosted client (claude.ai, chatgpt.com):
    1. Point your client at $MCP_URL/mcp
    2. Complete the OAuth dance — DCR happens automatically
    3. Approve the new client at /admin/remote-mcp on the dashboard
       (sign in to OpenAlgo first)
    4. Sign in to OpenAlgo when prompted to authorize the requested scopes

  Order placement is OFF by default. To enable on this instance:
    sudo sed -i "s|MCP_OAUTH_WRITE_SCOPE_ENABLED.*|MCP_OAUTH_WRITE_SCOPE_ENABLED = 'True'|" $ENV_FILE
    cd $STACK_DIR && docker compose restart
    Then re-authorize the client (OAuth tokens don't grow scope on refresh).

  For multi-instance deployments, re-run this script and pick a different
  stack each time — each instance gets its own OAuth signing keys + tables.

  See install/Remote-MCP-readme.md for the full design + threat model.
EOF

```


---

# FILE: install\install-docker-multi-custom-ssl.sh

```sh
#!/bin/bash

# OpenAlgo Docker Multi-Instance Installation with Custom SSL
# Supports deploying multiple instances with existing SSL certificates (including Wildcards)

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Base Configuration
INSTALL_BASE="/opt/openalgo"
START_FLASK_PORT=5000
START_WS_PORT=8765

# Script Banner
echo -e "${BLUE}"
echo "  ██████╗ ██████╗ ███████╗███╗   ██╗ █████╗ ██╗      ██████╗  ██████╗ "
echo " ██╔═══██╗██╔══██╗██╔════╝████╗  ██║██╔══██╗██║     ██╔════╝ ██╔═══██╗"
echo " ██║   ██║██████╔╝███████╗██╔██╗ ██║███████║██║     ██║  ███╗██║   ██║"
echo " ██║   ██║██╔═══╝ ██╔══╝  ██║╚██╗██║██╔══██║██║     ██║   ██║██║   ██║"
echo " ╚██████╔╝██╗     ███████╗██║ ╚████║██║  ██║███████╗╚██████╔╝╚██████╔╝"
echo "  ╚═════╝ ╚═╝     ╚══════╝╚═╝  ╚═══╝╚═╝  ╚═╝╚══════╝ ╚═════╝  ╚═════╝ "
echo "             MULTI-INSTANCE DOCKER + CUSTOM SSL INSTALLER               "
echo -e "${NC}"

# -----------------
# Helper Functions
# -----------------

log() {
    echo -e "${2}${1}${NC}"
}

check_status() {
    if [ $? -ne 0 ]; then
        log "Error: $1" "$RED"
        exit 1
    fi
}

generate_hex() {
    python3 -c "import secrets; print(secrets.token_hex(32))"
}

validate_broker() {
    local broker=$1
    local valid_brokers="fivepaisa,fivepaisaxts,aliceblue,angel,compositedge,definedge,deltaexchange,dhan,dhan_sandbox,firstock,flattrade,fyers,groww,ibulls,iifl,iiflcapital,indmoney,jainamxts,kotak,motilal,mstock,nubra,paytm,pocketful,rmoney,samco,shoonya,tradejini,upstox,wisdom,zebu,zerodha"
    [[ ",$valid_brokers," == *",$broker,"* ]]
}

is_xts_broker() {
    local broker=$1
    local xts_brokers="fivepaisaxts,compositedge,ibulls,iifl,jainamxts,rmoney,wisdom"
    if [[ ",$xts_brokers," == *",$broker,"* ]]; then
        return 0
    else
        return 1
    fi
}

sanitize_domain() {
    echo "$1" | tr '.' '-'
}

get_next_ports() {
    # Scan existing docker-compose files to find highest used ports
    local max_flask=$((START_FLASK_PORT - 1))
    local max_ws=$((START_WS_PORT - 1))
    
    # Check if base directory exists
    if [ -d "$INSTALL_BASE" ]; then
        # Find all docker-compose.yaml files
        while IFS= read -r file; do
            # Extract ports using grep/sed (simple parsing)
            local f_port=$(grep -A 5 "ports:" "$file" | grep ":5000" | cut -d: -f2)
            local w_port=$(grep -A 5 "ports:" "$file" | grep ":8765" | cut -d: -f2)
            
            # Update max if higher
            if [ ! -z "$f_port" ] && [ "$f_port" -gt "$max_flask" ]; then
                max_flask=$f_port
            fi
            if [ ! -z "$w_port" ] && [ "$w_port" -gt "$max_ws" ]; then
                max_ws=$w_port
            fi
        done < <(find "$INSTALL_BASE" -name "docker-compose.yaml")
    fi

    # Return next available pair
    echo "$((max_flask + 1)) $((max_ws + 1))"
}

# -----------------
# System Prep
# -----------------

# Check root
if [[ $EUID -ne 0 ]]; then
   log "This script must be run as root" "$RED" 
   exit 1
fi

log "\n=== System Preparation ===" "$BLUE"

# Update system
log "Updating system packages..." "$YELLOW"
apt-get update -y && apt-get upgrade -y
check_status "System update failed"

# Install basics
log "Installing dependencies..." "$YELLOW"
apt-get install -y \
    apt-transport-https \
    ca-certificates \
    curl \
    gnupg \
    lsb-release \
    git \
    nginx \
    ufw \
    python3-full \
    python3-pip
check_status "Package installation failed"

# Host Timezone Check
log "Checking Host Timezone..." "$YELLOW"
CURRENT_TZ=$(timedatectl show --property=Timezone --value 2>/dev/null || cat /etc/timezone)
if [[ "$CURRENT_TZ" != *"Asia/Kolkata"* ]]; then
    log "Setting Host Timezone to Asia/Kolkata..." "$YELLOW"
    timedatectl set-timezone Asia/Kolkata
    check_status "Failed to set timezone"
    log "Timezone set to Asia/Kolkata" "$GREEN"
else
    log "Host Timezone is already Asia/Kolkata." "$GREEN"
fi

# Install Docker
if ! command -v docker &> /dev/null; then
    log "Installing Docker..." "$YELLOW"
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    rm get-docker.sh
    check_status "Docker installation failed"
else
    log "Docker already installed" "$GREEN"
fi

# Install uv (if not present, though Docker installs it inside container, we might need it for utilities)
if ! command -v uv &> /dev/null; then
     log "Installing uv..." "$YELLOW"
     curl -LsSf https://astral.sh/uv/install.sh | sh
     if [ -f "$HOME/.cargo/env" ]; then
         source "$HOME/.cargo/env"
     fi
fi


# -----------------
# Configuration Collection
# -----------------

log "\n=== Configuration ===" "$BLUE"

# 0. Git Repository Selection
DEFAULT_REPO="https://github.com/marketcalls/openalgo.git"
read -p "Enter Git Repository URL [Default: $DEFAULT_REPO]: " REPO_URL
REPO_URL=${REPO_URL:-$DEFAULT_REPO}
log "Using Repository: $REPO_URL" "$GREEN"

# 1. Get Domains
while true; do
    read -p "Enter domain names separated by SPACE (e.g., domain.com zerodha.domain.com): " -a DOMAINS_INPUT
    if [ ${#DOMAINS_INPUT[@]} -eq 0 ]; then
        log "Error: At least one domain is required" "$RED"
        continue
    fi
    break
done

# 2. First Pass: Determine which domains are updates vs fresh installs
declare -a NEW_DOMAINS
declare -a UPDATE_DOMAINS

for DOMAIN in "${DOMAINS_INPUT[@]}"; do
    INSTANCE_DIR="$INSTALL_BASE/$DOMAIN"
    if [ -d "$INSTANCE_DIR" ] && [ -d "$INSTANCE_DIR/.git" ] && [ -f "$INSTANCE_DIR/.env" ]; then
        log "Found existing installation: $DOMAIN" "$GREEN"
        UPDATE_DOMAINS+=("$DOMAIN")
    else
        NEW_DOMAINS+=("$DOMAIN")
    fi
done

log "Update domains: ${#UPDATE_DOMAINS[@]}, New domains: ${#NEW_DOMAINS[@]}" "$BLUE"

# 3. Wildcard SSL Check - Only ask if there are NEW domains to configure
WILDCARD_CERT_PATH=""
WILDCARD_KEY_PATH=""
USE_WILDCARD_SSL="n"

if [ ${#NEW_DOMAINS[@]} -gt 0 ]; then
    log "\n${#NEW_DOMAINS[@]} new domain(s) detected. SSL configuration required." "$YELLOW"
    read -p "Do you have a WILDCARD SSL certificate for these domains? (y/n): " USE_WILDCARD_SSL

    if [[ $USE_WILDCARD_SSL =~ ^[Yy]$ ]]; then
        while true; do
            read -e -p "Enter path to Wildcard FULL CHAIN .pem file: " WILDCARD_CERT_PATH
            if [ ! -f "$WILDCARD_CERT_PATH" ]; then
                log "Error: File not found at $WILDCARD_CERT_PATH" "$RED"
                continue
            fi
            break
        done

        while true; do
            read -e -p "Enter path to Wildcard PRIVATE KEY .key file: " WILDCARD_KEY_PATH
            if [ ! -f "$WILDCARD_KEY_PATH" ]; then
                log "Error: File not found at $WILDCARD_KEY_PATH" "$RED"
                continue
            fi
            break
        done
    fi
else
    log "\nAll domains are existing installations - SSL configuration will be preserved." "$GREEN"
fi

# Arrays to store config
declare -a CONF_DOMAINS
declare -a CONF_BROKERS
declare -a CONF_API_KEYS
declare -a CONF_API_SECRETS
declare -a CONF_MARKET_KEYS
declare -a CONF_MARKET_SECRETS
declare -a CONF_SSL_CERTS
declare -a CONF_SSL_KEYS
declare -a UPDATE_MODE  # Track update vs fresh install per domain

# Helper function to extract value from .env file
extract_env_value() {
    local env_file="$1"
    local key="$2"
    grep "^${key}" "$env_file" 2>/dev/null | head -1 | cut -d"'" -f2 | tr -d "'" || echo ""
}

# 3. Iterate Domains for Config
for DOMAIN in "${DOMAINS_INPUT[@]}"; do
    log "\n--- Configuring Instance: $DOMAIN ---" "$YELLOW"

    # Check existing installation
    INSTANCE_DIR="$INSTALL_BASE/$DOMAIN"
    IS_UPDATE="false"
    
    if [ -d "$INSTANCE_DIR" ] && [ -d "$INSTANCE_DIR/.git" ]; then
        read -p "Instance for $DOMAIN already exists. Update code only? (y=update, n=skip, r=reinstall): " UPDATE_CHOICE
        case "$UPDATE_CHOICE" in
            [Yy]*)
                IS_UPDATE="true"
                log "Update mode: Will pull latest code and preserve configuration." "$GREEN"
                
                # Load existing configuration from .env
                EXISTING_ENV="$INSTANCE_DIR/.env"
                if [ -f "$EXISTING_ENV" ]; then
                    log "Loading existing configuration from .env..." "$GREEN"
                    EXISTING_BROKER=$(extract_env_value "$EXISTING_ENV" "REDIRECT_URL" | sed 's|.*/\([^/]*\)/callback|\1|')
                    EXISTING_API_KEY=$(extract_env_value "$EXISTING_ENV" "BROKER_API_KEY")
                    EXISTING_API_SECRET=$(extract_env_value "$EXISTING_ENV" "BROKER_API_SECRET")
                    EXISTING_M_KEY=$(extract_env_value "$EXISTING_ENV" "BROKER_API_KEY_MARKET")
                    EXISTING_M_SECRET=$(extract_env_value "$EXISTING_ENV" "BROKER_API_SECRET_MARKET")
                    
                    # Use existing values
                    CONF_DOMAINS+=("$DOMAIN")
                    CONF_BROKERS+=("$EXISTING_BROKER")
                    CONF_API_KEYS+=("$EXISTING_API_KEY")
                    CONF_API_SECRETS+=("$EXISTING_API_SECRET")
                    CONF_MARKET_KEYS+=("${EXISTING_M_KEY:-}")
                    CONF_MARKET_SECRETS+=("${EXISTING_M_SECRET:-}")
                    UPDATE_MODE+=("true")
                    
                    # SSL already configured, get existing paths
                    SSL_DIR="/etc/nginx/ssl/$DOMAIN"
                    if [ -f "$SSL_DIR/fullchain.pem" ]; then
                        CONF_SSL_CERTS+=("$SSL_DIR/fullchain.pem")
                        CONF_SSL_KEYS+=("$SSL_DIR/privkey.pem")
                    else
                        log "Warning: SSL certs not found, will need reconfiguration" "$YELLOW"
                        CONF_SSL_CERTS+=("EXISTING")
                        CONF_SSL_KEYS+=("EXISTING")
                    fi
                    
                    log "Loaded: Broker=$EXISTING_BROKER" "$GREEN"
                    continue  # Skip interactive prompts for this domain
                else
                    log "Warning: No .env found, treating as fresh install" "$YELLOW"
                    IS_UPDATE="false"
                fi
                ;;
            [Nn]*)
                log "Skipping $DOMAIN" "$YELLOW"
                continue
                ;;
            [Rr]*)
                log "Reinstall mode: Will ask for all configuration again." "$YELLOW"
                log "Warning: This will regenerate security keys and invalidate existing passwords!" "$RED"
                read -p "Are you sure you want to reinstall? (yes to confirm): " CONFIRM_REINSTALL
                if [ "$CONFIRM_REINSTALL" != "yes" ]; then
                    log "Skipping $DOMAIN" "$YELLOW"
                    continue
                fi
                ;;
            *)
                log "Invalid choice. Skipping $DOMAIN" "$RED"
                continue
                ;;
        esac
    fi
    
    # Mark as fresh install if not update mode
    UPDATE_MODE+=("$IS_UPDATE")

    CONF_DOMAINS+=("$DOMAIN")

    # Broker
    while true; do
        read -p "Enter BROKER for $DOMAIN: " BROKER
        if validate_broker "$BROKER"; then
            CONF_BROKERS+=("$BROKER")
            break
        else
            log "Invalid broker path. See documentation for list." "$RED"
        fi
    done

    # Credentials
    log "Redirect URL: https://$DOMAIN/$BROKER/callback" "$GREEN"
    # Credentials
    log "Redirect URL: https://$DOMAIN/$BROKER/callback" "$GREEN"
    while true; do
        read -p "Enter API Key: " API_KEY
        if [ ! -z "$API_KEY" ]; then
            CONF_API_KEYS+=("$API_KEY")
            break
        else
            log "API Key cannot be empty." "$RED"
        fi
    done

    while true; do
        read -p "Enter API Secret: " API_SECRET
        if [ ! -z "$API_SECRET" ]; then
            CONF_API_SECRETS+=("$API_SECRET")
            break
        else
            log "API Secret cannot be empty." "$RED"
        fi
    done

    # XTS Check
    if is_xts_broker "$BROKER"; then
        read -p "Enter Market Data API Key: " M_KEY
        read -p "Enter Market Data API Secret: " M_SECRET
        CONF_MARKET_KEYS+=("$M_KEY")
        CONF_MARKET_SECRETS+=("$M_SECRET")
    else
        CONF_MARKET_KEYS+=("")
        CONF_MARKET_SECRETS+=("")
    fi

    # SSL Config
    if [[ $USE_WILDCARD_SSL =~ ^[Yy]$ ]]; then
        CONF_SSL_CERTS+=("$WILDCARD_CERT_PATH")
        CONF_SSL_KEYS+=("$WILDCARD_KEY_PATH")
    else
        log "SSL Configuration for $DOMAIN" "$BLUE"
        echo "Select SSL Type:"
        echo "1) Custom SSL (You have your own .pem/.key files)"
        echo "2) Let's Encrypt (Automated via Certbot)"
         read -p "Enter choice [1/2] (Default: 1): " SSL_CHOICE
        SSL_CHOICE=${SSL_CHOICE:-1}

        if [ "$SSL_CHOICE" == "2" ]; then
             # Let's Encrypt
             CONF_SSL_CERTS+=("LETSENCRYPT_AUTO")
             CONF_SSL_KEYS+=("LETSENCRYPT_AUTO")
        else
             # Custom SSL with default suggestion
             DEFAULT_CERT_PATH="/etc/ssl/certs/${DOMAIN}.pem" # Example default
             DEFAULT_KEY_PATH="/etc/ssl/private/${DOMAIN}.key" # Example default
             
             # Try to find if user has a standard 'certs' folder in home or root
             if [ -d "$HOME/certs" ]; then
                 DEFAULT_CERT_PATH="$HOME/certs/${DOMAIN}.crt"
                 DEFAULT_KEY_PATH="$HOME/certs/${DOMAIN}.key"
             elif [ -d "/root/certs" ]; then
                 DEFAULT_CERT_PATH="/root/certs/${DOMAIN}.crt"
                 DEFAULT_KEY_PATH="/root/certs/${DOMAIN}.key"
             fi

             while true; do
                 read -e -p "Enter path to SSL Certificate [Default: $DEFAULT_CERT_PATH]: " CERT_PATH
                 CERT_PATH=${CERT_PATH:-$DEFAULT_CERT_PATH}
                 if [ ! -f "$CERT_PATH" ]; then
                     log "Error: File not found at $CERT_PATH" "$RED"
                     continue
                 fi
                 break
             done

             while true; do
                 read -e -p "Enter path to SSL Private Key [Default: $DEFAULT_KEY_PATH]: " KEY_PATH
                 KEY_PATH=${KEY_PATH:-$DEFAULT_KEY_PATH}
                 if [ ! -f "$KEY_PATH" ]; then
                     log "Error: File not found at $KEY_PATH" "$RED"
                     continue
                 fi
                 break
             done
             CONF_SSL_CERTS+=("$CERT_PATH")
             CONF_SSL_KEYS+=("$KEY_PATH")
         fi
    fi
done

# -----------------
# Deployment Loop
# -----------------

log "\n=== Starting Deployment ===" "$BLUE"

# Calculate dynamic resource limits based on system specs and number of instances
TOTAL_RAM_MB=$(($(grep MemTotal /proc/meminfo | awk '{print $2}') / 1024))
CPU_CORES=$(nproc 2>/dev/null || echo 2)
NUM_INSTANCES=${#CONF_DOMAINS[@]}

# Calculate per-instance RAM (divide total by number of instances)
RAM_PER_INSTANCE=$((TOTAL_RAM_MB / NUM_INSTANCES))
log "System: ${TOTAL_RAM_MB}MB RAM, ${CPU_CORES} cores, ${NUM_INSTANCES} instances" "$BLUE"
log "Per-instance allocation: ~${RAM_PER_INSTANCE}MB" "$BLUE"

# shm_size: 25% of per-instance RAM (min 128MB, max 1GB for multi-instance)
SHM_SIZE_MB=$((RAM_PER_INSTANCE / 4))
[ $SHM_SIZE_MB -lt 128 ] && SHM_SIZE_MB=128
[ $SHM_SIZE_MB -gt 1024 ] && SHM_SIZE_MB=1024

# Thread limits based on per-instance RAM (conservative)
# <2GB: 1 thread | 2-4GB: 2 threads | 4GB+: max(2, min(4, cores/instances))
if [ $RAM_PER_INSTANCE -lt 2000 ]; then
    THREAD_LIMIT=1
elif [ $RAM_PER_INSTANCE -lt 4000 ]; then
    THREAD_LIMIT=2
else
    CORES_PER_INSTANCE=$((CPU_CORES / NUM_INSTANCES))
    THREAD_LIMIT=$((CORES_PER_INSTANCE < 2 ? 2 : CORES_PER_INSTANCE))
    [ $THREAD_LIMIT -gt 4 ] && THREAD_LIMIT=4
fi

# Strategy memory limit based on per-instance RAM
# <2GB: 256MB | 2-4GB: 512MB | 4GB+: 1024MB
if [ $RAM_PER_INSTANCE -lt 2000 ]; then
    STRATEGY_MEM_LIMIT=256
elif [ $RAM_PER_INSTANCE -lt 4000 ]; then
    STRATEGY_MEM_LIMIT=512
else
    STRATEGY_MEM_LIMIT=1024
fi

log "Config: shm=${SHM_SIZE_MB}MB, threads=${THREAD_LIMIT}, strategy_mem=${STRATEGY_MEM_LIMIT}MB" "$BLUE"

# Base Dir
mkdir -p "$INSTALL_BASE"
chmod 755 "$INSTALL_BASE"

# Firewall Init (Open standard ports)
ufw allow ssh
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable

# Optional Portainer Installation - Smart Detection
PORTAINER_RUNNING=$(docker ps -q -f name=portainer)
PORTAINER_EXISTS=$(docker ps -aq -f name=portainer)
INSTALL_PORTAINER="n"
PORTAINER_DOMAIN=""

if [ ! -z "$PORTAINER_RUNNING" ]; then
    # Portainer is already running
    CURRENT_IMAGE=$(docker inspect portainer --format '{{.Config.Image}}' 2>/dev/null || echo "unknown")
    log "Portainer is already running (Image: $CURRENT_IMAGE)" "$GREEN"
    
    read -p "Check for Portainer updates? (y/n): " CHECK_PORTAINER_UPDATE
    if [[ $CHECK_PORTAINER_UPDATE =~ ^[Yy]$ ]]; then
        log "Checking for Portainer updates..." "$YELLOW"
        docker pull portainer/portainer-ce:latest
        
        NEW_IMAGE_ID=$(docker inspect portainer/portainer-ce:latest --format '{{.Id}}' 2>/dev/null | cut -c8-19)
        OLD_IMAGE_ID=$(docker inspect portainer --format '{{.Image}}' 2>/dev/null | cut -c8-19)
        
        if [ "$NEW_IMAGE_ID" != "$OLD_IMAGE_ID" ] && [ ! -z "$NEW_IMAGE_ID" ]; then
            log "New Portainer version available. Updating..." "$YELLOW"
            
            # Get current binding (preserve domain/IP configuration)
            CURRENT_BIND=$(docker port portainer 9000 2>/dev/null | cut -d: -f1)
            BIND_IP="${CURRENT_BIND:-127.0.0.1}"
            
            docker stop portainer && docker rm portainer
            docker run -d -p $BIND_IP:9000:9000 --name portainer --restart=always \
                -v /var/run/docker.sock:/var/run/docker.sock \
                -v portainer_data:/data \
                portainer/portainer-ce:latest
            log "Portainer updated successfully!" "$GREEN"
        else
            log "Portainer is already at latest version." "$GREEN"
        fi
    fi
    
    # Skip all further Portainer prompts - already configured
    INSTALL_PORTAINER="skip"
    
elif [ ! -z "$PORTAINER_EXISTS" ]; then
    # Portainer container exists but is stopped
    log "Portainer container exists but is stopped." "$YELLOW"
    read -p "Start existing Portainer? (y/n): " START_PORTAINER
    if [[ $START_PORTAINER =~ ^[Yy]$ ]]; then
        docker start portainer
        log "Portainer started." "$GREEN"
    fi
    INSTALL_PORTAINER="skip"
    
else
    # Fresh install option
    read -p "Do you want to install Portainer (Docker Management UI)? (y/n): " INSTALL_PORTAINER
fi

if [[ $INSTALL_PORTAINER =~ ^[Yy]$ ]]; then
    read -p "Enter Domain for Portainer (Leave EMPTY to use IP:9000): " PORTAINER_DOMAIN
    
    log "\nInstalling Portainer..." "$BLUE"
    
    # 1. Install Portainer Container
    if [ ! "$(docker ps -q -f name=portainer)" ]; then
        if [ "$(docker ps -aq -f status=exited -f name=portainer)" ]; then
            docker rm portainer
        fi
        
        docker volume create portainer_data
        # Run on localhost:9000 only if using Nginx, otherwise 0.0.0.0:9000
        if [ ! -z "$PORTAINER_DOMAIN" ]; then
            BIND_IP="127.0.0.1"
            log "Configuring Portainer for domain: $PORTAINER_DOMAIN" "$GREEN"
        else
            BIND_IP="0.0.0.0"
            ufw allow 9000/tcp
            log "Configuring Portainer for IP Access (Port 9000)" "$YELLOW"
        fi
        
        docker run -d -p $BIND_IP:9000:9000 --name portainer --restart=always \
            -v /var/run/docker.sock:/var/run/docker.sock \
            -v portainer_data:/data \
            portainer/portainer-ce:latest
            
    else
        log "Portainer is already running." "$YELLOW"
    fi

    # 2. Configure Nginx for Portainer (If domain provided)
    if [ ! -z "$PORTAINER_DOMAIN" ]; then
        # SSL Selection for Portainer
        P_SSL_CERT=""
        P_SSL_KEY=""
        P_SSL_MODE="none"
        
        echo "Select SSL Type for Portainer:"
        echo "1) Custom SSL (You have your own .pem/.key files)"
        echo "2) Let's Encrypt (Automated via Certbot)"
        echo "3) None (HTTP only - Not Recommended)"
        read -p "Enter choice [1/2/3] (Default: 1): " P_SSL_CHOICE
        P_SSL_CHOICE=${P_SSL_CHOICE:-1}

        if [ "$P_SSL_CHOICE" == "2" ]; then
             P_SSL_MODE="letsencrypt"
             P_SSL_CERT="LETSENCRYPT_AUTO"
             P_SSL_KEY="LETSENCRYPT_AUTO"
        elif [ "$P_SSL_CHOICE" == "1" ]; then
             P_SSL_MODE="custom"
             
             # Check for Wildcard match
             if [[ $USE_WILDCARD_SSL =~ ^[Yy]$ ]]; then
                 read -p "Use the same Wildcard SSL for Portainer? (y/n): " USE_WC_PORTAINER
                 if [[ $USE_WC_PORTAINER =~ ^[Yy]$ ]]; then
                     P_SSL_CERT="$WILDCARD_CERT_PATH"
                     P_SSL_KEY="$WILDCARD_KEY_PATH"
                 fi
             fi
             
             if [ -z "$P_SSL_CERT" ]; then
                 # Custom SSL with default suggestion
                 DEFAULT_P_CERT="/etc/ssl/certs/${PORTAINER_DOMAIN}.pem"
                 DEFAULT_P_KEY="/etc/ssl/private/${PORTAINER_DOMAIN}.key"
                 
                 if [ -d "$HOME/certs" ]; then
                     DEFAULT_P_CERT="$HOME/certs/${PORTAINER_DOMAIN}.crt"
                     DEFAULT_P_KEY="$HOME/certs/${PORTAINER_DOMAIN}.key"
                 elif [ -d "/root/certs" ]; then
                     DEFAULT_P_CERT="/root/certs/${PORTAINER_DOMAIN}.crt"
                     DEFAULT_P_KEY="/root/certs/${PORTAINER_DOMAIN}.key"
                 fi

                 while true; do
                     read -e -p "Enter path to Portainer SSL Certificate [Default: $DEFAULT_P_CERT]: " P_SSL_CERT
                     P_SSL_CERT=${P_SSL_CERT:-$DEFAULT_P_CERT}
                     if [ ! -f "$P_SSL_CERT" ]; then
                         log "Error: File not found at $P_SSL_CERT" "$RED"
                         continue
                     fi
                     break
                 done

                while true; do
                    read -e -p "Enter path to Portainer SSL Private Key [Default: $DEFAULT_P_KEY]: " P_SSL_KEY
                    P_SSL_KEY=${P_SSL_KEY:-$DEFAULT_P_KEY}
                    if [ ! -f "$P_SSL_KEY" ]; then
                        log "Error: File not found at $P_SSL_KEY" "$RED"
                        continue
                    fi
                    break
                done
            fi
        else
            log "Warning: Portainer will be deployed without SSL." "$YELLOW"
        fi

        
        # Setup SSL Dir
        P_SSL_DIR="/etc/nginx/ssl/$PORTAINER_DOMAIN"
        mkdir -p "$P_SSL_DIR"

        if [ "$P_SSL_CERT" == "LETSENCRYPT_AUTO" ]; then
             log "Generating Let's Encrypt SSL for Portainer ($PORTAINER_DOMAIN)..." "$YELLOW"
             
             # Ensure Certbot installed
             if ! command -v certbot &> /dev/null; then
                 apt-get install -y certbot
             fi
             
             systemctl stop nginx 2>/dev/null
             
             certbot certonly --standalone -d "$PORTAINER_DOMAIN" --non-interactive --agree-tos --register-unsafely-without-email
             
             LE_CERT="/etc/letsencrypt/live/$PORTAINER_DOMAIN/fullchain.pem"
             LE_KEY="/etc/letsencrypt/live/$PORTAINER_DOMAIN/privkey.pem"
             
            if [ -f "$LE_CERT" ]; then
                log "Portainer SSL Generated Successfully" "$GREEN"
                cp -L "$LE_CERT" "$P_SSL_DIR/fullchain.pem"
                cp -L "$LE_KEY" "$P_SSL_DIR/privkey.pem"
            else
                log "Error: Portainer Let's Encrypt generation failed." "$RED"
                # Fallback or exit? user might want to continue. Let's exit to be safe.
                exit 1
            fi
        else
            cp "$P_SSL_CERT" "$P_SSL_DIR/fullchain.pem"
            cp "$P_SSL_KEY" "$P_SSL_DIR/privkey.pem"
        fi
        
        chmod 600 "$P_SSL_DIR/privkey.pem"
        chmod 644 "$P_SSL_DIR/fullchain.pem"

        # Create Nginx Config
        cat <<EOF > "/etc/nginx/sites-available/$PORTAINER_DOMAIN"
server {
    listen 80;
    server_name $PORTAINER_DOMAIN;
    return 301 https://\$host\$request_uri;
}

server {
    listen 443 ssl http2;
    server_name $PORTAINER_DOMAIN;

    ssl_certificate $P_SSL_DIR/fullchain.pem;
    ssl_certificate_key $P_SSL_DIR/privkey.pem;
    
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers EECDH+AESGCM:EDH+AESGCM;
    ssl_prefer_server_ciphers on;
    
    location / {
        proxy_pass http://127.0.0.1:9000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF
        ln -sf "/etc/nginx/sites-available/$PORTAINER_DOMAIN" "/etc/nginx/sites-enabled/"
        log "Portainer Nginx configuration created." "$GREEN"
    fi
fi

for i in "${!CONF_DOMAINS[@]}"; do
    DOMAIN="${CONF_DOMAINS[$i]}"
    BROKER="${CONF_BROKERS[$i]}"
    API_KEY="${CONF_API_KEYS[$i]}"
    API_SECRET="${CONF_API_SECRETS[$i]}"
    M_KEY="${CONF_MARKET_KEYS[$i]}"
    M_SECRET="${CONF_MARKET_SECRETS[$i]}"
    SSL_CERT="${CONF_SSL_CERTS[$i]}"
    SSL_KEY="${CONF_SSL_KEYS[$i]}"

    log "\nDeploying $DOMAIN..." "$BLUE"

    # 1. Allocation
    INSTANCE_DIR="$INSTALL_BASE/$DOMAIN"
    PORTS=($(get_next_ports))
    FLASK_PORT=${PORTS[0]}
    WS_PORT=${PORTS[1]}
    SANITIZED_NAME=$(sanitize_domain "$DOMAIN")
    PROJECT_NAME="openalgo-${SANITIZED_NAME}"

    log " -> Ports: Flask=$FLASK_PORT, WS=$WS_PORT" "$GREEN"
    log " -> Dir: $INSTANCE_DIR" "$GREEN"

    # 3. SSL Setup
    SSL_DIR="/etc/nginx/ssl/$DOMAIN"
    mkdir -p "$SSL_DIR"

    if [ "$SSL_CERT" == "LETSENCRYPT_AUTO" ]; then
        log "Generating Let's Encrypt SSL for $DOMAIN..." "$YELLOW"
        
        # Ensure Certbot installed
        if ! command -v certbot &> /dev/null; then
            log "Installing Certbot..." "$YELLOW"
            apt-get install -y certbot
        fi

        # Stop Nginx for standalone mode
        systemctl stop nginx 2>/dev/null
        
        # Run Certbot
        certbot certonly --standalone -d "$DOMAIN" --non-interactive --agree-tos --register-unsafely-without-email
        
        LE_CERT="/etc/letsencrypt/live/$DOMAIN/fullchain.pem"
        LE_KEY="/etc/letsencrypt/live/$DOMAIN/privkey.pem"
        
        if [ -f "$LE_CERT" ]; then
            log "Let's Encrypt Certificate Generated Successfully" "$GREEN"
            cp -L "$LE_CERT" "$SSL_DIR/fullchain.pem"
            cp -L "$LE_KEY" "$SSL_DIR/privkey.pem"
        else
            log "Error: Let's Encrypt generation failed." "$RED"
            exit 1
        fi
    else
        # Custom SSL
        cp "$SSL_CERT" "$SSL_DIR/fullchain.pem"
        cp "$SSL_KEY" "$SSL_DIR/privkey.pem"
    fi

    chmod 600 "$SSL_DIR/privkey.pem"
    chmod 644 "$SSL_DIR/fullchain.pem"
    
    # 4. Clone/Update Repo
    if [ ! -d "$INSTANCE_DIR/.git" ]; then
        if [ -d "$INSTANCE_DIR" ]; then
            log "Directory exists but is not a valid git repo. Backing up and re-cloning..." "$YELLOW"
            mv "$INSTANCE_DIR" "${INSTANCE_DIR}_backup_$(date +%s)"
        fi
        git clone "$REPO_URL" "$INSTANCE_DIR"
    else
        log "Updating existing repository..." "$GREEN"
        cd "$INSTANCE_DIR"
        # Force sync with the selected repo URL to pick up Dockerfile fixes
        git remote set-url origin "$REPO_URL"
        git fetch origin
        git reset --hard origin/main
    fi
    
    mkdir -p "$INSTANCE_DIR"/{log,logs,keys,db,strategies/scripts,strategies/examples}
    
    # 5. Env Config - CRITICAL: Preserve .env during updates to maintain passwords
    IS_UPDATE_MODE="${UPDATE_MODE[$i]}"
    ENV_FILE="$INSTANCE_DIR/.env"
    
    if [ "$IS_UPDATE_MODE" == "true" ] && [ -f "$ENV_FILE" ]; then
        log "Preserving existing .env file (keeps APP_KEY, PEPPER, and passwords valid)" "$GREEN"
        
        # Only update connectivity settings if needed (in case domain changed)
        # These are safe to update without breaking authentication
        sed -i "s|WEBSOCKET_URL='.*'|WEBSOCKET_URL='wss://$DOMAIN/ws'|g" "$ENV_FILE"
        
        # CORS: Add domain if not already present (preserves custom domains like chart.domain.com)
        # NOTE: Flask-CORS expects comma-separated origins (see cors.py line 25)
        if ! grep "CORS_ALLOWED_ORIGINS" "$ENV_FILE" | grep -q "https://$DOMAIN"; then
            # Extract current CORS value and append new domain with comma
            CURRENT_CORS=$(grep "CORS_ALLOWED_ORIGINS" "$ENV_FILE" | sed "s/.*= '\\(.*\\)'/\\1/")
            if [ -n "$CURRENT_CORS" ]; then
                NEW_CORS="$CURRENT_CORS,https://$DOMAIN"
                # Remove duplicates while preserving comma format
                NEW_CORS=$(echo "$NEW_CORS" | tr ',' '\n' | sort -u | tr '\n' ',' | sed 's/,$//')
                sed -i "s|CORS_ALLOWED_ORIGINS = '.*'|CORS_ALLOWED_ORIGINS = '$NEW_CORS'|g" "$ENV_FILE"
            fi
        fi
        
        # CSP: Add domain if not already present (delete-and-append avoids sed regex issues with nested quotes)
        # See: https://github.com/marketcalls/openalgo/issues/938
        if ! grep "CSP_CONNECT_SRC" "$ENV_FILE" | grep -q "https://$DOMAIN"; then
            CURRENT_CSP=$(grep "^CSP_CONNECT_SRC" "$ENV_FILE" | sed 's/^CSP_CONNECT_SRC *= *//; s/^"//; s/"$//')
            if [ -n "$CURRENT_CSP" ] && ! echo "$CURRENT_CSP" | grep -q "https://$DOMAIN"; then
                NEW_CSP="$CURRENT_CSP https://$DOMAIN wss://$DOMAIN"
                sed -i '/^CSP_CONNECT_SRC/d' "$ENV_FILE"
                echo "CSP_CONNECT_SRC = \"$NEW_CSP\"" >> "$ENV_FILE"
            fi
        fi
        
        log "Updated connectivity settings (preserved custom domains)" "$GREEN"
    else
        log "Creating new .env configuration..." "$YELLOW"
        cp "$INSTANCE_DIR/.sample.env" "$ENV_FILE"
        
        APP_KEY=$(generate_hex)
        PEPPER=$(generate_hex)
        
        sed -i "s|YOUR_BROKER_API_KEY|$API_KEY|g" "$ENV_FILE"
        sed -i "s|YOUR_BROKER_API_SECRET|$API_SECRET|g" "$ENV_FILE"
        sed -i "s|http://127.0.0.1:5000|https://$DOMAIN|g" "$ENV_FILE"
        sed -i "s|<broker>|$BROKER|g" "$ENV_FILE"
        sed -i "s|OPENALGO_PLACEHOLDER_APP_KEY_REGENERATE_BEFORE_USE|$APP_KEY|g" "$ENV_FILE"
        sed -i "s|OPENALGO_PLACEHOLDER_API_KEY_PEPPER_REGENERATE_BEFORE_USE|$PEPPER|g" "$ENV_FILE"

        # Capture build-time git info for the diagnostics page (issue #1388).
        # .git/ is dockerignored, so the running container has no .git/HEAD;
        # surface the values via env from the cloned source instead.
        GIT_BRANCH=$(cd "$INSTANCE_DIR" && git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "")
        GIT_COMMIT=$(cd "$INSTANCE_DIR" && git rev-parse --short HEAD 2>/dev/null || echo "")
        echo "OPENALGO_GIT_BRANCH = '${GIT_BRANCH}'" >> "$ENV_FILE"
        echo "OPENALGO_GIT_COMMIT = '${GIT_COMMIT}'" >> "$ENV_FILE"
        # Each instance is published only on 127.0.0.1 with nginx in front;
        # trust the proxy's X-Forwarded-For / X-Real-IP.
        sed -i "s|TRUST_PROXY_HEADERS = 'FALSE'|TRUST_PROXY_HEADERS = 'TRUE'|g" "$ENV_FILE"
        # .env is bind-mounted read+write into the container so auto-rotation
        # of compromised APP_KEY/API_KEY_PEPPER (utils/env_check.py) can run.
        # Container runs as appuser (UID 1000); chown to UID 1000 + chmod 600
        # gives appuser read+write while keeping the file private on the host.
        chown 1000:1000 "$ENV_FILE"
        chmod 600 "$ENV_FILE"
        
        # XTS
        if [ ! -z "$M_KEY" ]; then
            sed -i "s|YOUR_BROKER_MARKET_API_KEY|$M_KEY|g" "$ENV_FILE"
            sed -i "s|YOUR_BROKER_MARKET_API_SECRET|$M_SECRET|g" "$ENV_FILE"
        fi
        
        # Connectivity
        sed -i "s|WEBSOCKET_URL='.*'|WEBSOCKET_URL='wss://$DOMAIN/ws'|g" "$ENV_FILE"
        # WEBSOCKET_HOST / FLASK_HOST_IP bind to 0.0.0.0 inside the container so
        # the Docker port mapping can route traffic from the host's nginx.
        sed -i "s|WEBSOCKET_HOST='127.0.0.1'|WEBSOCKET_HOST='0.0.0.0'|g" "$ENV_FILE"
        sed -i "s|FLASK_HOST_IP='127.0.0.1'|FLASK_HOST_IP='0.0.0.0'|g" "$ENV_FILE"
        # ZMQ_HOST stays on loopback: internal message bus, same-container only.
        # Exposing it would leak the raw tick feed.
        sed -i "s|CORS_ALLOWED_ORIGINS = '.*'|CORS_ALLOWED_ORIGINS = 'https://$DOMAIN'|g" "$ENV_FILE"
        # CSP: Set connect sources with domain (delete-and-append avoids sed regex issues with nested quotes)
        # See: https://github.com/marketcalls/openalgo/issues/938
        sed -i '/^CSP_CONNECT_SRC/d' "$ENV_FILE"
        echo "CSP_CONNECT_SRC = \"'self' wss://$DOMAIN https://$DOMAIN wss: ws: https://cdn.socket.io\"" >> "$ENV_FILE"
        
        log "New .env created with fresh security keys" "$GREEN"
    fi

    # 6. Docker Compose
    cat <<EOF > "$INSTANCE_DIR/docker-compose.yaml"
services:
  openalgo:
    image: ${PROJECT_NAME}:latest
    build:
      context: .
      dockerfile: Dockerfile
    container_name: ${PROJECT_NAME}-web
    ports:
      - "127.0.0.1:${FLASK_PORT}:5000"
      - "127.0.0.1:${WS_PORT}:8765"
    volumes:
      - openalgo_db:/app/db
      - openalgo_log:/app/log
      - openalgo_strategies:/app/strategies
      - openalgo_keys:/app/keys
      - openalgo_tmp:/app/tmp
      - ./.env:/app/.env
    environment:
      - FLASK_ENV=production
      - FLASK_DEBUG=0
      - APP_MODE=standalone
      - TZ=Asia/Kolkata
      # Resource limits auto-calculated for multi-instance deployment
      # See: https://github.com/marketcalls/openalgo/issues/822
      - OPENBLAS_NUM_THREADS=${THREAD_LIMIT}
      - OMP_NUM_THREADS=${THREAD_LIMIT}
      - MKL_NUM_THREADS=${THREAD_LIMIT}
      - NUMEXPR_NUM_THREADS=${THREAD_LIMIT}
      - NUMBA_NUM_THREADS=${THREAD_LIMIT}
      - STRATEGY_MEMORY_LIMIT_MB=${STRATEGY_MEM_LIMIT}
    shm_size: '${SHM_SIZE_MB}m'
    healthcheck:
      test: ["CMD", "curl", "-f", "http://127.0.0.1:5000/auth/check-setup"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    restart: unless-stopped

volumes:
  openalgo_db:
    driver: local
  openalgo_log:
    driver: local
  openalgo_strategies:
    driver: local
  openalgo_keys:
    driver: local
  openalgo_tmp:
    driver: local
EOF

    # 7. Nginx Config
    cat <<EOF > "/etc/nginx/sites-available/$DOMAIN"
upstream openalgo_flask_${SANITIZED_NAME} {
    server 127.0.0.1:${FLASK_PORT};
    keepalive 64;
}

upstream openalgo_websocket_${SANITIZED_NAME} {
    server 127.0.0.1:${WS_PORT};
    keepalive 64;
}

server {
    listen 80;
    server_name $DOMAIN;
    return 301 https://\$host\$request_uri;
}

server {
    listen 443 ssl http2;
    server_name $DOMAIN;

    ssl_certificate $SSL_DIR/fullchain.pem;
    ssl_certificate_key $SSL_DIR/privkey.pem;
    
    # Modern SSL Config
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers EECDH+AESGCM:EDH+AESGCM;
    ssl_prefer_server_ciphers on;
    ssl_session_timeout 1d;
    ssl_session_cache shared:SSL:10m;
    
    # Security Headers
    add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    
    client_max_body_size 50M;

    # Logic: WebSocket
    location = /ws {
        proxy_pass http://openalgo_websocket_${SANITIZED_NAME};
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_read_timeout 86400s;
    }
    location /ws/ {
        proxy_pass http://openalgo_websocket_${SANITIZED_NAME}/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_read_timeout 86400s;
    }

    # Logic: Socket.IO (Flask-SocketIO real-time events)
    location /socket.io/ {
        proxy_pass http://openalgo_flask_${SANITIZED_NAME}/socket.io/;
        proxy_http_version 1.1;
        proxy_read_timeout 86400s;
        proxy_send_timeout 86400s;
        proxy_buffering off;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    # Logic: Main App
    location / {
        proxy_pass http://openalgo_flask_${SANITIZED_NAME};
        proxy_http_version 1.1;
        proxy_read_timeout 300s;
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;

        # Increased buffer sizes for large headers (auth tokens, session cookies)
        proxy_buffer_size 128k;
        proxy_buffers 4 256k;
        proxy_busy_buffers_size 256k;

        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF
    
    # Activate Nginx
    ln -sf "/etc/nginx/sites-available/$DOMAIN" "/etc/nginx/sites-enabled/"
    
    # 8. Service Start
    log "Starting Container for $DOMAIN..." "$BLUE"
    log "Building Docker image (includes automated frontend build, may take 2-5 minutes)..." "$YELLOW"
    cd "$INSTANCE_DIR"
    docker compose build
    docker compose up -d
    
done

# Restart Nginx to load new configs
log "Reloading Nginx..." "$YELLOW"
nginx -t && systemctl reload nginx
check_status "Nginx reload failed"


# -----------------
# Management Tool
# -----------------

cat <<'EOF' > /usr/local/bin/openalgo-ctl
#!/bin/bash
# OpenAlgo Manager

INSTALL_BASE="/opt/openalgo"

cmd=$1
target=$2

list_instances() {
    echo "INSTALLED INSTANCES:"
    echo "--------------------"
    for d in $INSTALL_BASE/*/; do
        [ -d "$d" ] || continue
        dom=$(basename "$d")
        # skip backup folders
        if [[ "$dom" == *"_backup_"* ]]; then
             continue
        fi
        status=$(cd "$d" && docker compose ps --format "{{.Status}}" 2>/dev/null)
        echo "$dom : ${status:-STOPPED}"
    done
}

usage() {
    echo "Usage: openalgo-ctl <command> [domain]"
    echo "Commands:"
    echo "  list              - List all instances"
    echo "  restart <domain>  - Restart specific instance"
    echo "  logs <domain>     - Show logs for instance"
    echo "  status <domain>   - Show status"
}

if [ "$cmd" == "list" ]; then
    list_instances
    exit 0
fi

if [ -z "$target" ]; then
    usage
    exit 1
fi

TARGET_DIR="$INSTALL_BASE/$target"
if [ ! -d "$TARGET_DIR" ]; then
    echo "Error: Instance $target not found."
    exit 1
fi

case "$cmd" in
    restart)
        cd "$TARGET_DIR" && docker compose restart
        ;;
    logs)
        cd "$TARGET_DIR" && docker compose logs -f --tail=100
        ;;
    status)
        cd "$TARGET_DIR" && docker compose ps
        ;;
    stop)
        cd "$TARGET_DIR" && docker compose stop
        ;;
    start)
        cd "$TARGET_DIR" && docker compose start
        ;;
    *)
        usage
        exit 1
        ;;
esac
EOF

chmod +x /usr/local/bin/openalgo-ctl


log "\n==============================================" "$GREEN"
log " INSTALLATION COMPLETE" "$GREEN"
log "==============================================" "$GREEN"
log "Management Command: openalgo-ctl" "$BLUE"
log "  openalgo-ctl list" "$BLUE"
log "  openalgo-ctl restart <domain.com>" "$BLUE"
log "  openalgo-ctl logs <domain.com>" "$BLUE"

log "\n[IMPORTANT] CLOUD FIREWALL SETTINGS:" "$YELLOW"
log "Ensure the following Inbound Ports are OPEN in your Azure NSG / AWS Security Group:" "$RED"
log "  - TCP 80 (HTTP)" "$NC"
log "  - TCP 443 (HTTPS)" "$NC"
log "  - TCP 22 (SSH)" "$NC"
if [[ $INSTALL_PORTAINER =~ ^[Yy]$ ]]; then
    if [ -z "$PORTAINER_DOMAIN" ]; then
        log "  - TCP 9000 (Portainer UI)" "$NC"
    fi
fi
log "\nAccess your instances via their respective HTTPS domains." "$GREEN"

```


---

# FILE: install\install-docker.sh

```sh
#!/bin/bash

# OpenAlgo Docker Installation Script
# Simplified installation for Docker deployment with custom domain

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# OpenAlgo Banner
echo -e "${BLUE}"
echo "  ██████╗ ██████╗ ███████╗███╗   ██╗ █████╗ ██╗      ██████╗  ██████╗ "
echo " ██╔═══██╗██╔══██╗██╔════╝████╗  ██║██╔══██╗██║     ██╔════╝ ██╔═══██╗"
echo " ██║   ██║██████╔╝███████╗██╔██╗ ██║███████║██║     ██║  ███╗██║   ██║"
echo " ██║   ██║██╔═══╝ ██╔══╝  ██║╚██╗██║██╔══██║██║     ██║   ██║██║   ██║"
echo " ╚██████╔╝██╗     ███████╗██║ ╚████║██║  ██║███████╗╚██████╔╝╚██████╔╝"
echo "  ╚═════╝ ╚═╝     ╚══════╝╚═╝  ╚═══╝╚═╝  ╚═╝╚══════╝ ╚═════╝  ╚═════╝ "      
echo "                    DOCKER INSTALLATION                                 "
echo -e "${NC}"

# Function to log messages
log() {
    echo -e "${2}${1}${NC}"
}

# Function to check command status
check_status() {
    if [ $? -ne 0 ]; then
        log "Error: $1" "$RED"
        exit 1
    fi
}

# Function to generate random hex string
generate_hex() {
    python3 -c "import secrets; print(secrets.token_hex(32))"
}

# Function to validate broker
validate_broker() {
    local broker=$1
    local valid_brokers="fivepaisa,fivepaisaxts,aliceblue,angel,compositedge,definedge,deltaexchange,dhan,dhan_sandbox,firstock,flattrade,fyers,groww,ibulls,iifl,iiflcapital,indmoney,jainamxts,kotak,motilal,mstock,nubra,paytm,pocketful,rmoney,samco,shoonya,tradejini,upstox,wisdom,zebu,zerodha"
    [[ ",$valid_brokers," == *",$broker,"* ]]
}

# Function to check if broker is XTS based
is_xts_broker() {
    local broker=$1
    local xts_brokers="fivepaisaxts,compositedge,ibulls,iifl,jainamxts,rmoney,wisdom"
    [[ ",$xts_brokers," == *",$broker,"* ]]
}

# Start installation
log "Starting OpenAlgo Docker Installation..." "$GREEN"
log "========================================" "$GREEN"

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   log "WARNING: Running as root user is not recommended for production." "$YELLOW"
   log "For better security, consider creating a non-root user with sudo privileges." "$YELLOW"
   read -p "Do you want to continue as root? (y/n): " continue_as_root
   if [[ ! $continue_as_root =~ ^[Yy]$ ]]; then
       log "Installation cancelled. Create a non-root user with:" "$BLUE"
       log "  adduser yourusername" "$BLUE"
       log "  usermod -aG sudo yourusername" "$BLUE"
       log "  su - yourusername" "$BLUE"
       exit 0
   fi
   log "Continuing as root user..." "$YELLOW"
   SUDO=""
else
   SUDO="sudo"
fi

# Check OS
if [ ! -f /etc/os-release ]; then
    log "Unsupported operating system" "$RED"
    exit 1
fi

OS_TYPE=$(grep -w "ID" /etc/os-release | cut -d "=" -f 2 | tr -d '"')
log "Detected OS: $OS_TYPE" "$BLUE"

# Support Ubuntu/Debian for now
if [[ "$OS_TYPE" != "ubuntu" && "$OS_TYPE" != "debian" ]]; then
    log "This script currently supports Ubuntu/Debian. Detected: $OS_TYPE" "$YELLOW"
    read -p "Do you want to continue anyway? (y/n): " continue_anyway
    if [[ ! $continue_anyway =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Collect installation information
log "\n=== Installation Configuration ===" "$BLUE"

# Get domain name
while true; do
    read -p "Enter your domain name (e.g., demo.openalgo.in): " DOMAIN
    if [ -z "$DOMAIN" ]; then
        log "Error: Domain name is required" "$RED"
        continue
    fi
    if [[ ! $DOMAIN =~ ^[a-zA-Z0-9]([a-zA-Z0-9-]*[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9-]*[a-zA-Z0-9])?)*\.[a-zA-Z]{2,}$ ]]; then
        log "Error: Invalid domain format" "$RED"
        continue
    fi
    break
done

# Get broker name
while true; do
    log "\nValid brokers:" "$BLUE"
    echo "fivepaisa, fivepaisaxts, aliceblue, angel, compositedge, definedge, deltaexchange,"
    echo "dhan, dhan_sandbox, firstock, flattrade, fyers, groww, ibulls, iifl, iiflcapital,"
    echo "indmoney, jainamxts, kotak, motilal, mstock, nubra, paytm, pocketful,"
    echo "rmoney, samco, shoonya, tradejini, upstox, wisdom, zebu, zerodha,"
    echo ""
    read -p "Enter your broker name: " BROKER_NAME
    if validate_broker "$BROKER_NAME"; then
        break
    else
        log "Invalid broker name. Please choose from the list above." "$RED"
    fi
done

# Show redirect URL
log "\n=== Broker API Setup ===" "$YELLOW"
log "Redirect URL for broker developer portal:" "$BLUE"
log "https://$DOMAIN/$BROKER_NAME/callback" "$GREEN"
log "\nUse this URL in your broker's developer portal to get API credentials." "$BLUE"
echo ""

# Get broker API credentials
read -p "Enter your broker API key: " BROKER_API_KEY
read -p "Enter your broker API secret: " BROKER_API_SECRET

if [ -z "$BROKER_API_KEY" ] || [ -z "$BROKER_API_SECRET" ]; then
    log "Error: Broker API credentials are required" "$RED"
    exit 1
fi

# Check if XTS broker and get additional credentials
BROKER_API_KEY_MARKET=""
BROKER_API_SECRET_MARKET=""
if is_xts_broker "$BROKER_NAME"; then
    log "\nThis broker requires additional market data credentials." "$YELLOW"
    read -p "Enter your broker market data API key: " BROKER_API_KEY_MARKET
    read -p "Enter your broker market data API secret: " BROKER_API_SECRET_MARKET
    
    if [ -z "$BROKER_API_KEY_MARKET" ] || [ -z "$BROKER_API_SECRET_MARKET" ]; then
        log "Error: Market data API credentials are required for XTS brokers" "$RED"
        exit 1
    fi
fi

# Get email for SSL certificate
read -p "Enter your email for SSL certificate notifications: " ADMIN_EMAIL
if [ -z "$ADMIN_EMAIL" ]; then
    ADMIN_EMAIL="admin@${DOMAIN#*.}"
fi

# Optional: Remote MCP for hosted AI clients (Claude.ai, ChatGPT).
# Same-domain mode — /mcp and /oauth/* are served from the same nginx
# vhost as the dashboard, so the existing reverse-proxy config covers it.
# Local stdio MCP (Claude Desktop / Cursor / Windsurf) works regardless.
log "\nRemote MCP lets hosted AI clients (Claude.ai, ChatGPT) connect to OpenAlgo over HTTPS." "$BLUE"
log "Skip this if you only use the local MCP server with Claude Desktop / Cursor." "$YELLOW"
read -p "Enable Remote MCP? (y/N): " enable_mcp_input
ENABLE_REMOTE_MCP="false"
if [[ $enable_mcp_input =~ ^[Yy]$ ]]; then
    ENABLE_REMOTE_MCP="true"
    log "Remote MCP will be enabled at https://$DOMAIN/mcp" "$GREEN"
fi

# Generate security keys
log "\nGenerating security keys..." "$BLUE"
APP_KEY=$(generate_hex)
API_KEY_PEPPER=$(generate_hex)

# Set installation path
INSTALL_PATH="/opt/openalgo"

log "\n=== Installation Summary ===" "$YELLOW"
log "Domain: $DOMAIN" "$BLUE"
log "Broker: $BROKER_NAME" "$BLUE"
log "Installation Path: $INSTALL_PATH" "$BLUE"
log "Email: $ADMIN_EMAIL" "$BLUE"
echo ""

read -p "Proceed with installation? (y/n): " proceed
if [[ ! $proceed =~ ^[Yy]$ ]]; then
    log "Installation cancelled." "$YELLOW"
    exit 0
fi

# Update system
log "\n=== Updating System ===" "$BLUE"
$SUDO apt-get update -y
$SUDO apt-get upgrade -y
check_status "System update failed"

# Install required packages
log "\n=== Installing Required Packages ===" "$BLUE"
$SUDO apt-get install -y \
    apt-transport-https \
    ca-certificates \
    curl \
    gnupg \
    lsb-release \
    git \
    nginx \
    certbot \
    python3-certbot-nginx \
    ufw
check_status "Package installation failed"

# Install Docker
log "\n=== Installing Docker ===" "$BLUE"
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com -o get-docker.sh
    $SUDO sh get-docker.sh
    $SUDO usermod -aG docker $USER
    rm get-docker.sh
    check_status "Docker installation failed"
else
    log "Docker already installed" "$GREEN"
fi

# Verify Docker Compose
if ! docker compose version &> /dev/null; then
    log "Error: Docker Compose not found" "$RED"
    exit 1
fi
log "Docker Compose version: $(docker compose version --short)" "$GREEN"

# Clone OpenAlgo repository
log "\n=== Cloning OpenAlgo Repository ===" "$BLUE"
if [ -d "$INSTALL_PATH" ]; then
    log "Warning: $INSTALL_PATH already exists" "$YELLOW"
    read -p "Remove existing installation? (y/n): " remove_existing
    if [[ $remove_existing =~ ^[Yy]$ ]]; then
        $SUDO rm -rf $INSTALL_PATH
    else
        log "Installation cancelled" "$RED"
        exit 1
    fi
fi

$SUDO git clone https://github.com/marketcalls/openalgo.git $INSTALL_PATH
check_status "Git clone failed"

cd $INSTALL_PATH

# Create required directories
log "\n=== Creating Required Directories ===" "$BLUE"
$SUDO mkdir -p log logs keys db strategies/scripts strategies/examples
$SUDO chown -R 1000:1000 log logs strategies db
$SUDO chmod -R 755 strategies log db
$SUDO chmod 700 keys
check_status "Directory creation failed"

# Configure environment file
log "\n=== Configuring Environment File ===" "$BLUE"
$SUDO cp .sample.env .env

# Update .env file
$SUDO sed -i "s|YOUR_BROKER_API_KEY|$BROKER_API_KEY|g" .env
$SUDO sed -i "s|YOUR_BROKER_API_SECRET|$BROKER_API_SECRET|g" .env
$SUDO sed -i "s|http://127.0.0.1:5000|https://$DOMAIN|g" .env
$SUDO sed -i "s|<broker>|$BROKER_NAME|g" .env
$SUDO sed -i "s|OPENALGO_PLACEHOLDER_APP_KEY_REGENERATE_BEFORE_USE|$APP_KEY|g" .env
$SUDO sed -i "s|OPENALGO_PLACEHOLDER_API_KEY_PEPPER_REGENERATE_BEFORE_USE|$API_KEY_PEPPER|g" .env

# Capture build-time git info for the diagnostics page (issue #1388).
# .git/ is dockerignored, so the running container has no .git/HEAD to read —
# we surface the values via env instead. Both lines are appended only when not
# already present so re-runs of this script don't accumulate duplicates.
GIT_BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "")
GIT_COMMIT=$(git rev-parse --short HEAD 2>/dev/null || echo "")
if ! grep -qE "^OPENALGO_GIT_BRANCH\s*=" .env 2>/dev/null; then
    echo "OPENALGO_GIT_BRANCH = '${GIT_BRANCH}'" | $SUDO tee -a .env > /dev/null
fi
if ! grep -qE "^OPENALGO_GIT_COMMIT\s*=" .env 2>/dev/null; then
    echo "OPENALGO_GIT_COMMIT = '${GIT_COMMIT}'" | $SUDO tee -a .env > /dev/null
fi

# Container is published only on 127.0.0.1:5000 with nginx in front; trust the
# proxy's X-Forwarded-For / X-Real-IP so IP-based features see the real client.
$SUDO sed -i "s|TRUST_PROXY_HEADERS = 'FALSE'|TRUST_PROXY_HEADERS = 'TRUE'|g" .env

# .env is bind-mounted read+write into the container at /app/.env so the
# auto-rotation in utils/env_check.py can replace publicly-known APP_KEY /
# API_KEY_PEPPER values on first run (see issue #1039 follow-up). The
# container runs as `appuser` (UID 1000 from the Dockerfile), so chown the
# file to UID 1000 and tighten to 0600 — only appuser can read or write it
# from inside the container, and the file is no longer world-readable on
# the host. Earlier versions used mode 644 because the mount was :ro and
# 600 + root ownership made it unreadable to UID 1000 (issue #960). With
# the mount switched to read-write and the file owned by UID 1000, 600 is
# both safe and necessary.
$SUDO chown 1000:1000 .env
$SUDO chmod 600 .env

# Update XTS market data credentials if applicable
if is_xts_broker "$BROKER_NAME"; then
    $SUDO sed -i "s|YOUR_BROKER_MARKET_API_KEY|$BROKER_API_KEY_MARKET|g" .env
    $SUDO sed -i "s|YOUR_BROKER_MARKET_API_SECRET|$BROKER_API_SECRET_MARKET|g" .env
fi

# Update WebSocket and host configurations
$SUDO sed -i "s|WEBSOCKET_URL='.*'|WEBSOCKET_URL='wss://$DOMAIN/ws'|g" .env
# WEBSOCKET_HOST / FLASK_HOST_IP must be 0.0.0.0 *inside* the container so the
# Docker port mapping (-p host:container) can route traffic. nginx on the host
# reverse-proxies /ws and / onto these ports over the Docker bridge.
$SUDO sed -i "s|WEBSOCKET_HOST='127.0.0.1'|WEBSOCKET_HOST='0.0.0.0'|g" .env
$SUDO sed -i "s|FLASK_HOST_IP='127.0.0.1'|FLASK_HOST_IP='0.0.0.0'|g" .env
# ZMQ_HOST is NOT rewritten: ZeroMQ is an internal message bus between broker
# adapters and the WS proxy, both of which run in the same container. Keeping
# it on loopback prevents the raw tick feed from being reachable via any port
# that might be accidentally exposed.
# CORS: Add domain if not already present (preserves custom domains)
# NOTE: Flask-CORS expects comma-separated origins (see cors.py line 25)
if ! grep "CORS_ALLOWED_ORIGINS" .env | grep -q "https://$DOMAIN"; then
    CURRENT_CORS=$(grep "CORS_ALLOWED_ORIGINS" .env | sed "s/.*= '\\(.*\\)'/\\1/")
    if [ -n "$CURRENT_CORS" ]; then
        NEW_CORS="$CURRENT_CORS,https://$DOMAIN"
        NEW_CORS=$(echo "$NEW_CORS" | tr ',' '\n' | sort -u | tr '\n' ',' | sed 's/,$//')
        $SUDO sed -i "s|CORS_ALLOWED_ORIGINS = '.*'|CORS_ALLOWED_ORIGINS = '$NEW_CORS'|g" .env
    fi
fi

# CSP: Set connect sources with domain (delete-and-append avoids sed regex issues with nested quotes)
# See: https://github.com/marketcalls/openalgo/issues/938
$SUDO sed -i '/^CSP_CONNECT_SRC/d' .env
echo "CSP_CONNECT_SRC = \"'self' wss: ws: https://cdn.socket.io https://$DOMAIN wss://$DOMAIN\"" | $SUDO tee -a .env > /dev/null

# Enable Remote MCP if the operator opted in. Same-domain mode: /mcp and
# /oauth/* are served from the same nginx vhost as the dashboard, no
# extra config needed. Other MCP_* keys (auto-approve, write scope, CORS
# allowlist) inherit their defaults from .sample.env — flip them later
# in .env if you want stricter behavior on a shared deployment.
if [ "$ENABLE_REMOTE_MCP" = "true" ]; then
    $SUDO sed -i "s|MCP_HTTP_ENABLED = 'False'|MCP_HTTP_ENABLED = 'True'|g" .env
    $SUDO sed -i "s|MCP_PUBLIC_URL = ''|MCP_PUBLIC_URL = 'https://$DOMAIN'|g" .env
    log "Remote MCP enabled at https://$DOMAIN/mcp" "$GREEN"
fi

check_status "Environment configuration failed"

# Calculate dynamic resource limits based on system specs
TOTAL_RAM_MB=$(($(grep MemTotal /proc/meminfo | awk '{print $2}') / 1024))
CPU_CORES=$(nproc 2>/dev/null || echo 2)

# shm_size: 25% of RAM (min 256MB, max 2GB)
SHM_SIZE_MB=$((TOTAL_RAM_MB / 4))
[ $SHM_SIZE_MB -lt 256 ] && SHM_SIZE_MB=256
[ $SHM_SIZE_MB -gt 2048 ] && SHM_SIZE_MB=2048

# Thread limits based on RAM (conservative for strategy subprocess compatibility)
# 2GB: 1 thread | 4GB: 2 threads | 8GB+: min(4, cores)
if [ $TOTAL_RAM_MB -lt 3000 ]; then
    THREAD_LIMIT=1
elif [ $TOTAL_RAM_MB -lt 6000 ]; then
    THREAD_LIMIT=2
else
    THREAD_LIMIT=$((CPU_CORES < 4 ? CPU_CORES : 4))
fi

# Strategy memory limit based on RAM
# 2GB: 256MB | 4GB: 512MB | 8GB+: 1024MB
if [ $TOTAL_RAM_MB -lt 3000 ]; then
    STRATEGY_MEM_LIMIT=256
elif [ $TOTAL_RAM_MB -lt 6000 ]; then
    STRATEGY_MEM_LIMIT=512
else
    STRATEGY_MEM_LIMIT=1024
fi

log "System: ${TOTAL_RAM_MB}MB RAM, ${CPU_CORES} cores" "$BLUE"
log "Config: shm=${SHM_SIZE_MB}MB, threads=${THREAD_LIMIT}, strategy_mem=${STRATEGY_MEM_LIMIT}MB" "$BLUE"

# Create docker-compose.yaml
log "\n=== Creating Docker Compose Configuration ===" "$BLUE"
$SUDO tee docker-compose.yaml > /dev/null << EOF
services:
  openalgo:
    image: openalgo:latest
    build:
      context: .
      dockerfile: Dockerfile

    container_name: openalgo-web

    ports:
      - "127.0.0.1:5000:5000"
      - "127.0.0.1:8765:8765"

    # Use named volumes to avoid permission issues with non-root container user
    volumes:
      - openalgo_db:/app/db
      - openalgo_log:/app/log
      - openalgo_strategies:/app/strategies
      - openalgo_keys:/app/keys
      - openalgo_tmp:/app/tmp
      - ./.env:/app/.env

    environment:
      - FLASK_ENV=production
      - FLASK_DEBUG=0
      - APP_MODE=standalone
      - TZ=Asia/Kolkata
      # Resource limits auto-calculated based on system specs
      # See: https://github.com/marketcalls/openalgo/issues/822
      - OPENBLAS_NUM_THREADS=${THREAD_LIMIT}
      - OMP_NUM_THREADS=${THREAD_LIMIT}
      - MKL_NUM_THREADS=${THREAD_LIMIT}
      - NUMEXPR_NUM_THREADS=${THREAD_LIMIT}
      - NUMBA_NUM_THREADS=${THREAD_LIMIT}
      - STRATEGY_MEMORY_LIMIT_MB=${STRATEGY_MEM_LIMIT}

    # Shared memory for scipy/numba operations (auto-calculated: 25% of RAM)
    shm_size: '${SHM_SIZE_MB}m'

    healthcheck:
      test: ["CMD", "curl", "-f", "http://127.0.0.1:5000/auth/check-setup"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

    restart: unless-stopped

# Named volumes for data persistence with proper permissions
volumes:
  openalgo_db:
    driver: local
  openalgo_log:
    driver: local
  openalgo_strategies:
    driver: local
  openalgo_keys:
    driver: local
  openalgo_tmp:
    driver: local
EOF

check_status "Docker Compose configuration failed"

# Configure firewall
log "\n=== Configuring Firewall ===" "$BLUE"
$SUDO ufw --force enable
$SUDO ufw default deny incoming
$SUDO ufw default allow outgoing
$SUDO ufw allow ssh
$SUDO ufw allow 80/tcp
$SUDO ufw allow 443/tcp
check_status "Firewall configuration failed"

# Initial Nginx configuration
log "\n=== Configuring Nginx (Initial) ===" "$BLUE"
$SUDO tee /etc/nginx/sites-available/$DOMAIN > /dev/null << EOF
server {
    listen 80;
    listen [::]:80;
    server_name $DOMAIN;
    
    location /.well-known/acme-challenge/ {
        root /var/www/html;
    }
    
    location / {
        return 301 https://\$server_name\$request_uri;
    }
}
EOF

$SUDO ln -sf /etc/nginx/sites-available/$DOMAIN /etc/nginx/sites-enabled/
$SUDO rm -f /etc/nginx/sites-enabled/default
$SUDO nginx -t
check_status "Nginx configuration test failed"

$SUDO systemctl enable nginx
$SUDO systemctl reload nginx
check_status "Nginx reload failed"

# Obtain SSL certificate
log "\n=== Obtaining SSL Certificate ===" "$BLUE"
log "Please wait while we obtain SSL certificate from Let's Encrypt..." "$YELLOW"
$SUDO certbot --nginx -d $DOMAIN --non-interactive --agree-tos --email $ADMIN_EMAIL
check_status "SSL certificate obtention failed"

# Final Nginx configuration with SSL
log "\n=== Configuring Nginx (Production with SSL) ===" "$BLUE"
$SUDO tee /etc/nginx/sites-available/$DOMAIN > /dev/null << EOF
# Rate limiting zones
limit_req_zone \$binary_remote_addr zone=api_limit:10m rate=50r/s;
limit_req_zone \$binary_remote_addr zone=general_limit:10m rate=10r/s;

# Upstream definitions
upstream openalgo_flask {
    server 127.0.0.1:5000;
    keepalive 64;
}

upstream openalgo_websocket {
    server 127.0.0.1:8765;
    keepalive 64;
}

# HTTP - Redirect to HTTPS
server {
    listen 80;
    listen [::]:80;
    server_name $DOMAIN;

    # Allow Certbot renewals
    location /.well-known/acme-challenge/ {
        root /var/www/html;
    }

    # WebSocket paths
    location = /ws {
        return 301 https://\$host\$request_uri;
    }

    location /ws/ {
        return 301 https://\$host\$request_uri;
    }

    # All other HTTP traffic
    location / {
        return 301 https://\$host\$request_uri;
    }
}

# HTTPS - Main Configuration
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    
    server_name $DOMAIN;
    
    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/$DOMAIN/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/$DOMAIN/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;
    
    # Security Headers
    add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    
    # Client settings
    client_max_body_size 100M;
    client_body_timeout 300s;
    
    # Logging
    access_log /var/log/nginx/${DOMAIN}_access.log;
    error_log /var/log/nginx/${DOMAIN}_error.log;

    # WebSocket Proxy Server (Port 8765)
    location = /ws {
        proxy_pass http://openalgo_websocket;
        proxy_http_version 1.1;
        proxy_read_timeout 86400s;
        proxy_send_timeout 86400s;
        proxy_connect_timeout 60s;
        proxy_buffering off;
        proxy_cache off;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_set_header X-Forwarded-Host \$host;
        proxy_set_header X-Forwarded-Port \$server_port;
        proxy_redirect off;
    }

    location /ws/ {
        proxy_pass http://openalgo_websocket/;
        proxy_http_version 1.1;
        proxy_read_timeout 86400s;
        proxy_send_timeout 86400s;
        proxy_connect_timeout 60s;
        proxy_buffering off;
        proxy_cache off;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_set_header X-Forwarded-Host \$host;
        proxy_set_header X-Forwarded-Port \$server_port;
        proxy_redirect off;
    }

    # Socket.IO WebSocket
    location /socket.io/ {
        proxy_pass http://openalgo_flask/socket.io/;
        proxy_http_version 1.1;
        proxy_read_timeout 86400s;
        proxy_send_timeout 86400s;
        proxy_connect_timeout 60s;
        proxy_buffering off;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_set_header X-Forwarded-Host \$host;
        proxy_set_header X-Forwarded-Port \$server_port;
        proxy_redirect off;
    }

    # API Endpoints
    location /api/ {
        limit_req zone=api_limit burst=100 nodelay;
        limit_req_status 429;
        proxy_pass http://openalgo_flask;
        proxy_http_version 1.1;
        proxy_read_timeout 300s;
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_set_header X-Forwarded-Host \$host;
        proxy_set_header X-Forwarded-Port \$server_port;
        proxy_set_header Connection "";
        proxy_redirect off;
    }

    # Static Files
    location /static/ {
        proxy_pass http://openalgo_flask;
        proxy_http_version 1.1;
        proxy_cache_valid 200 1d;
        proxy_cache_bypass \$http_pragma \$http_authorization;
        expires 1d;
        add_header Cache-Control "public, max-age=86400";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    # Main Application
    location / {
        limit_req zone=general_limit burst=20 nodelay;
        proxy_pass http://openalgo_flask;
        proxy_http_version 1.1;
        proxy_read_timeout 300s;
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_buffering off;

        # Increased buffer sizes for large headers (auth tokens, session cookies)
        proxy_buffer_size 128k;
        proxy_buffers 4 256k;
        proxy_busy_buffers_size 256k;

        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_set_header X-Forwarded-Host \$host;
        proxy_set_header X-Forwarded-Port \$server_port;
        proxy_set_header Connection "";
        proxy_redirect off;
    }

    # Deny hidden files
    location ~ /\. {
        deny all;
        access_log off;
        log_not_found off;
    }

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_types text/plain text/css text/xml text/javascript 
               application/json application/javascript application/xml+rss 
               application/x-javascript;
}
EOF

$SUDO nginx -t
check_status "Nginx configuration test failed"

$SUDO systemctl reload nginx
check_status "Nginx reload failed"

# Build and start Docker container
log "\n=== Building Docker Image ===" "$BLUE"
log "Includes automated frontend build. This may take 2-5 minutes depending on your server..." "$YELLOW"
sudo docker compose build
check_status "Docker build failed"

log "\n=== Starting Docker Container ===" "$BLUE"
sudo docker compose up -d
check_status "Docker container start failed"

# Wait for container to be healthy
log "\nWaiting for container to be healthy..." "$YELLOW"
sleep 10

# Check container status
CONTAINER_STATUS=$(sudo docker ps --filter "name=openalgo-web" --format "{{.Status}}")
if [[ $CONTAINER_STATUS == *"Up"* ]]; then
    log "Container started successfully!" "$GREEN"
else
    log "Warning: Container may not have started correctly" "$YELLOW"
    log "Check logs with: sudo docker compose logs -f" "$BLUE"
fi

# Create management scripts
log "\n=== Creating Management Scripts ===" "$BLUE"

# Status script
$SUDO tee /usr/local/bin/openalgo-status > /dev/null << 'EOFSCRIPT'
#!/bin/bash
echo "=========================================="
echo "OpenAlgo Status"
echo "=========================================="
echo ""
echo "Container Status:"
sudo docker ps --filter "name=openalgo-web" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
echo ""
echo "Container Health:"
sudo docker inspect openalgo-web --format='{{.State.Health.Status}}' 2>/dev/null || echo "Container not found"
echo ""
echo "Recent Logs:"
sudo docker compose -f /opt/openalgo/docker-compose.yaml logs --tail=30
EOFSCRIPT

$SUDO chmod +x /usr/local/bin/openalgo-status

# Restart script
$SUDO tee /usr/local/bin/openalgo-restart > /dev/null << 'EOFSCRIPT'
#!/bin/bash
echo "Restarting OpenAlgo..."
cd /opt/openalgo
sudo docker compose restart
sleep 10
echo "Container Status:"
sudo docker ps --filter "name=openalgo-web"
EOFSCRIPT

$SUDO chmod +x /usr/local/bin/openalgo-restart

# Logs script
$SUDO tee /usr/local/bin/openalgo-logs > /dev/null << 'EOFSCRIPT'
#!/bin/bash
cd /opt/openalgo
sudo docker compose logs -f --tail=100
EOFSCRIPT

$SUDO chmod +x /usr/local/bin/openalgo-logs

# Backup script
$SUDO tee /usr/local/bin/openalgo-backup > /dev/null << 'EOFSCRIPT'
#!/bin/bash
BACKUP_DIR="/opt/openalgo-backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/openalgo_backup_$TIMESTAMP.tar.gz"
mkdir -p $BACKUP_DIR
echo "Creating backup..."
cd /opt/openalgo

# Backup .env file and Docker volume data
echo "Backing up configuration and volume data..."
sudo docker compose stop

# Create temp directory for volume exports
TEMP_DIR=$(mktemp -d)

# Export data from Docker volumes
sudo docker run --rm -v openalgo_db:/data -v $TEMP_DIR:/backup alpine tar -czf /backup/db.tar.gz -C /data . 2>/dev/null
sudo docker run --rm -v openalgo_strategies:/data -v $TEMP_DIR:/backup alpine tar -czf /backup/strategies.tar.gz -C /data . 2>/dev/null

# Create final backup
sudo tar -czf $BACKUP_FILE .env -C $TEMP_DIR db.tar.gz strategies.tar.gz 2>/dev/null

# Cleanup temp directory
sudo rm -rf $TEMP_DIR

sudo docker compose start
echo "Backup created: $BACKUP_FILE"

# Keep only last 7 backups
cd $BACKUP_DIR
ls -t openalgo_backup_*.tar.gz 2>/dev/null | tail -n +8 | xargs -r rm
echo "Backup completed!"
EOFSCRIPT

$SUDO chmod +x /usr/local/bin/openalgo-backup

log "Management scripts created successfully!" "$GREEN"

# Setup SSL auto-renewal
log "\n=== Setting Up SSL Auto-Renewal ===" "$BLUE"
$SUDO mkdir -p /etc/letsencrypt/renewal-hooks/deploy
$SUDO tee /etc/letsencrypt/renewal-hooks/deploy/reload-nginx.sh > /dev/null << 'EOFSCRIPT'
#!/bin/bash
systemctl reload nginx
EOFSCRIPT
$SUDO chmod +x /etc/letsencrypt/renewal-hooks/deploy/reload-nginx.sh

# Installation complete
log "\n============================================" "$GREEN"
log "OpenAlgo Docker Installation Complete!" "$GREEN"
log "============================================" "$GREEN"

log "\nInstallation Summary:" "$YELLOW"
log "Domain: https://$DOMAIN" "$BLUE"
log "Broker: $BROKER_NAME" "$BLUE"
log "Installation Path: $INSTALL_PATH" "$BLUE"
log "Container: openalgo-web" "$BLUE"
if [ "$ENABLE_REMOTE_MCP" = "true" ]; then
    log "Remote MCP: Enabled at https://$DOMAIN/mcp" "$BLUE"
else
    log "Remote MCP: Disabled" "$BLUE"
fi

log "\nNext Steps:" "$YELLOW"
log "1. Visit https://$DOMAIN to access OpenAlgo" "$GREEN"
log "2. Create your admin account and login" "$GREEN"
log "3. Configure your broker settings" "$GREEN"

log "\nUseful Commands:" "$YELLOW"
log "View status:  openalgo-status" "$BLUE"
log "View logs:    openalgo-logs" "$BLUE"
log "Restart:      openalgo-restart" "$BLUE"
log "Backup:       openalgo-backup" "$BLUE"

log "\nDocker Commands:" "$YELLOW"
log "Restart:      cd $INSTALL_PATH && sudo docker compose restart" "$BLUE"
log "Stop:         cd $INSTALL_PATH && sudo docker compose stop" "$BLUE"
log "Start:        cd $INSTALL_PATH && sudo docker compose start" "$BLUE"
log "Rebuild:      cd $INSTALL_PATH && sudo docker compose down && sudo docker compose build --no-cache && sudo docker compose up -d" "$BLUE"

log "\nFor support, visit: https://discord.com/invite/UPh7QPsNhP" "$BLUE"

log "\n============================================" "$GREEN"
log "Installation completed successfully!" "$GREEN"
log "============================================" "$GREEN"

```


---

# FILE: install\install-multi.sh

```sh
#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# OpenAlgo Multi-Instance Installation Banner
echo -e "${BLUE}"
echo "  ██████╗ ██████╗ ███████╗███╗   ██╗ █████╗ ██╗      ██████╗  ██████╗ "
echo " ██╔═══██╗██╔══██╗██╔════╝████╗  ██║██╔══██╗██║     ██╔════╝ ██╔═══██╗"
echo " ██║   ██║██████╔╝███████╗██╔██╗ ██║███████║██║     ██║  ███╗██║   ██║"
echo " ██║   ██║██╔═══╝ ██╔══╝  ██║╚██╗██║██╔══██║██║     ██║   ██║██║   ██║"
echo " ╚██████╔╝██╗     ███████╗██║ ╚████║██║  ██║███████╗╚██████╔╝╚██████╔╝"
echo "  ╚═════╝ ╚═╝     ╚══════╝╚═╝  ╚═══╝╚═╝  ╚═╝╚══════╝ ╚═════╝  ╚═════╝ "
echo "                      MULTI-INSTANCE INSTALLER                          "
echo -e "${NC}"

# Create logs directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
LOGS_DIR="$SCRIPT_DIR/logs"
mkdir -p "$LOGS_DIR"

# Generate unique log file
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_FILE="$LOGS_DIR/install_multi_${TIMESTAMP}.log"

# Function to log messages
log_message() {
    local message="$1"
    local color="$2"
    echo -e "${color}${message}${NC}" | tee -a "$LOG_FILE"
}

# Function to check command status
check_status() {
    if [ $? -ne 0 ]; then
        log_message "Error: $1" "$RED"
        exit 1
    fi
}

# Function to generate random hex string
generate_hex() {
    python3 -c "import secrets; print(secrets.token_hex(32))"
}

# Function to validate broker name
validate_broker() {
    local broker=$1
    local valid_brokers="fivepaisa,fivepaisaxts,aliceblue,angel,compositedge,definedge,deltaexchange,dhan,dhan_sandbox,firstock,flattrade,fyers,groww,ibulls,iifl,iiflcapital,indmoney,jainamxts,kotak,motilal,mstock,nubra,paytm,pocketful,rmoney,samco,shoonya,tradejini,upstox,wisdom,zebu,zerodha"

    if [[ ",$valid_brokers," == *",$broker,"* ]]; then
        return 0
    else
        return 1
    fi
}

# Function to check if broker is XTS based
is_xts_broker() {
    local broker=$1
    local xts_brokers="fivepaisaxts,compositedge,ibulls,iifl,jainamxts,rmoney,wisdom"
    if [[ ",$xts_brokers," == *",$broker,"* ]]; then
        return 0
    else
        return 1
    fi
}

# Function to check timezone
check_timezone() {
    current_tz=$(timedatectl | grep "Time zone" | awk '{print $3}')
    log_message "Current timezone: $current_tz" "$BLUE"

    if [[ "$current_tz" == "Asia/Kolkata" ]]; then
        log_message "Server is already set to IST timezone." "$GREEN"
        return 0
    fi

    log_message "Server is not set to IST timezone." "$YELLOW"
    read -p "Would you like to change the timezone to IST? (y/n): " change_tz
    if [[ $change_tz =~ ^[Yy]$ ]]; then
        log_message "Changing timezone to IST..." "$BLUE"
        sudo timedatectl set-timezone Asia/Kolkata
        check_status "Failed to change timezone"
        log_message "Timezone successfully changed to IST" "$GREEN"
    else
        log_message "Keeping current timezone: $current_tz" "$YELLOW"
    fi
}

# Start logging
log_message "Starting OpenAlgo Multi-Instance installation" "$BLUE"
log_message "Log file: $LOG_FILE" "$BLUE"
log_message "----------------------------------------" "$BLUE"

# Check timezone
check_timezone

# Ask number of instances
while true; do
    read -p "How many OpenAlgo instances do you want to set up? " INSTANCES
    if [[ "$INSTANCES" =~ ^[0-9]+$ ]] && [ "$INSTANCES" -gt 0 ]; then
        break
    else
        log_message "❌ Invalid number. Please enter a positive integer." "$RED"
    fi
done

log_message "Setting up $INSTANCES OpenAlgo instances" "$GREEN"

# Base configuration
BASE_DIR="/var/python/openalgo-flask"
REPO_URL="https://github.com/marketcalls/openalgo.git"
FLASK_PORT_BASE=5000
WS_PORT_BASE=8765
ZMQ_PORT_BASE=5555

# Arrays to store instance configurations
declare -a DOMAINS
declare -a BROKERS
declare -a API_KEYS
declare -a API_SECRETS
declare -a API_KEYS_MARKET
declare -a API_SECRETS_MARKET
declare -a IS_XTS
declare -a MCP_ENABLED_LIST

# Collect information for all instances
log_message "\n=== COLLECTING INSTANCE CONFIGURATIONS ===" "$YELLOW"

for ((i=1; i<=INSTANCES; i++)); do
    log_message "\n--- Instance $i Configuration ---" "$BLUE"

    # Get domain
    while true; do
        read -p "Enter subdomain for instance $i (e.g., trade$i.example.com): " domain
        if [ -z "$domain" ]; then
            log_message "Error: Domain name is required" "$RED"
            continue
        fi
        # Simplified domain validation: must contain at least one dot and end with valid TLD
        if [[ ! $domain =~ ^[a-zA-Z0-9]([a-zA-Z0-9-]*[a-zA-Z0-9])?(\.([a-zA-Z0-9]([a-zA-Z0-9-]*[a-zA-Z0-9])?))+$ ]]; then
            log_message "Error: Invalid domain format (e.g., subdomain.example.com)" "$RED"
            continue
        fi
        DOMAINS+=("$domain")
        break
    done

    # Get broker
    while true; do
        log_message "\nValid brokers: fivepaisa,fivepaisaxts,aliceblue,angel,compositedge,definedge,deltaexchange,dhan,dhan_sandbox,firstock,flattrade,fyers,groww,ibulls,iifl,indmoney,jainamxts,kotak,motilal,mstock,nubra,paytm,pocketful,rmoney,samco,shoonya,tradejini,upstox,wisdom,zebu,zerodha" "$BLUE"
        read -p "Enter broker name for instance $i: " broker
        if validate_broker "$broker"; then
            BROKERS+=("$broker")
            break
        else
            log_message "Invalid broker name" "$RED"
        fi
    done

    # Show redirect URL
    log_message "\nRedirect URL for broker portal: https://${domain}/${broker}/callback" "$GREEN"
    echo ""

    # Get API credentials
    read -p "Enter broker API key for instance $i: " api_key
    read -p "Enter broker API secret for instance $i: " api_secret

    if [ -z "$api_key" ] || [ -z "$api_secret" ]; then
        log_message "Error: API credentials are required" "$RED"
        exit 1
    fi

    API_KEYS+=("$api_key")
    API_SECRETS+=("$api_secret")

    # Check for XTS broker
    if is_xts_broker "$broker"; then
        IS_XTS+=("true")
        log_message "\nThis broker ($broker) requires market data credentials" "$YELLOW"
        read -p "Enter market data API key: " market_key
        read -p "Enter market data API secret: " market_secret

        if [ -z "$market_key" ] || [ -z "$market_secret" ]; then
            log_message "Error: Market data credentials required for XTS brokers" "$RED"
            exit 1
        fi

        API_KEYS_MARKET+=("$market_key")
        API_SECRETS_MARKET+=("$market_secret")
    else
        IS_XTS+=("false")
        API_KEYS_MARKET+=("")
        API_SECRETS_MARKET+=("")
    fi

    # Optional: Remote MCP for hosted AI clients (Claude.ai, ChatGPT).
    # Same-domain mode — /mcp and /oauth/* are served from the same nginx
    # vhost as this instance's dashboard, so no extra config is required.
    # Local stdio MCP (Claude Desktop / Cursor / Windsurf) works regardless.
    log_message "\nRemote MCP lets hosted AI clients (Claude.ai, ChatGPT) connect to OpenAlgo over HTTPS." "$BLUE"
    log_message "Skip this if you only use the local MCP server with Claude Desktop / Cursor." "$YELLOW"
    read -p "Enable Remote MCP for instance $i? (y/N): " enable_mcp_input
    if [[ $enable_mcp_input =~ ^[Yy]$ ]]; then
        MCP_ENABLED_LIST+=("true")
        log_message "Remote MCP will be enabled at https://$domain/mcp" "$GREEN"
    else
        MCP_ENABLED_LIST+=("false")
    fi

    log_message "✅ Instance $i configuration collected" "$GREEN"
done

# System packages installation (one-time)
log_message "\n=== INSTALLING SYSTEM PACKAGES ===" "$YELLOW"
sudo apt-get update && sudo apt-get upgrade -y
check_status "Failed to update system"

sudo apt-get install -y python3 python3-venv python3-pip python3-full nginx git software-properties-common snapd ufw certbot python3-certbot-nginx \
    libopenblas0 libgomp1 libgfortran5
check_status "Failed to install packages"

# Install Chromium for Kaleido/Plotly static chart rendering (Telegram /chart command).
# Kaleido 1.x ships no bundled browser; it drives a system Chromium via choreographer.
# Debian has 'chromium' in main; Ubuntu 19.10+ renamed it to 'chromium-browser' (snap transitional).
# Non-fatal — if nothing sticks we warn; the rest of openalgo still installs fine.
log_message "\nInstalling Chromium for Telegram /chart rendering..." "$BLUE"
if sudo apt-get install -y chromium fonts-liberation 2>/dev/null; then
    log_message "Installed chromium (Debian package)" "$GREEN"
elif sudo apt-get install -y chromium-browser fonts-liberation 2>/dev/null; then
    log_message "Installed chromium-browser (Ubuntu transitional/snap)" "$GREEN"
else
    log_message "Chromium install failed - Telegram /chart will not render charts" "$YELLOW"
    log_message "You can install it manually later: sudo snap install chromium" "$YELLOW"
fi

# Install uv
log_message "\nInstalling uv package manager..." "$BLUE"
sudo snap install astral-uv --classic
check_status "Failed to install uv"

# Configure firewall (one-time)
log_message "\nConfiguring firewall..." "$BLUE"
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 'Nginx Full'
sudo ufw --force enable
check_status "Failed to configure firewall"

# Create base directory
sudo mkdir -p "$BASE_DIR"

# Install each instance
log_message "\n=== INSTALLING INSTANCES ===" "$YELLOW"

for ((i=1; i<=INSTANCES; i++)); do
    idx=$((i-1))
    DOMAIN="${DOMAINS[$idx]}"
    BROKER="${BROKERS[$idx]}"
    API_KEY="${API_KEYS[$idx]}"
    API_SECRET="${API_SECRETS[$idx]}"
    API_KEY_MARKET="${API_KEYS_MARKET[$idx]}"
    API_SECRET_MARKET="${API_SECRETS_MARKET[$idx]}"
    IS_XTS_INSTANCE="${IS_XTS[$idx]}"
    ENABLE_REMOTE_MCP="${MCP_ENABLED_LIST[$idx]}"

    log_message "\n--- Installing Instance $i: $DOMAIN ($BROKER) ---" "$BLUE"

    # Paths
    DEPLOY_NAME="${DOMAIN/./-}-${BROKER}"
    INSTANCE_DIR="$BASE_DIR/openalgo$i"
    VENV_PATH="$INSTANCE_DIR/venv"
    SOCKET_FILE="$INSTANCE_DIR/openalgo.sock"
    SERVICE_NAME="openalgo$i"

    # Ports
    FLASK_PORT=$((FLASK_PORT_BASE + i - 1))
    WS_PORT=$((WS_PORT_BASE + i - 1))
    ZMQ_PORT=$((ZMQ_PORT_BASE + i - 1))

    # Clone or update repository
    if [ ! -d "$INSTANCE_DIR" ]; then
        log_message "📥 Cloning repository to $INSTANCE_DIR" "$BLUE"
        sudo git clone "$REPO_URL" "$INSTANCE_DIR"
        check_status "Failed to clone repository"
    else
        log_message "⚠️ Directory exists, skipping clone" "$YELLOW"
    fi

    # Create virtual environment
    log_message "Setting up virtual environment..." "$BLUE"
    if [ -d "$VENV_PATH" ]; then
        sudo rm -rf "$VENV_PATH"
    fi
    sudo uv venv "$VENV_PATH"
    check_status "Failed to create venv"

    # Install dependencies
    log_message "Installing Python dependencies..." "$BLUE"
    ACTIVATE_CMD="source $VENV_PATH/bin/activate"
    sudo bash -c "$ACTIVATE_CMD && uv pip install -r $INSTANCE_DIR/requirements-nginx.txt"
    check_status "Failed to install dependencies"

    # Ensure gunicorn and eventlet
    sudo bash -c "$ACTIVATE_CMD && uv pip install 'gunicorn>=25.0,<26' eventlet"

    # Configure .env file
    log_message "Configuring environment file..." "$BLUE"
    ENV_FILE="$INSTANCE_DIR/.env"

    if [ -f "$ENV_FILE" ]; then
        sudo mv "$ENV_FILE" "${ENV_FILE}.backup_$(date +%Y%m%d_%H%M%S)"
    fi

    sudo cp "$INSTANCE_DIR/.sample.env" "$ENV_FILE"

    # Generate keys
    APP_KEY=$(generate_hex)
    API_KEY_PEPPER=$(generate_hex)

    # Database paths (unique per instance for complete isolation)
    DB_PATH="sqlite:///db/openalgo${i}.db"
    LATENCY_DB="sqlite:///db/latency${i}.db"
    LOGS_DB="sqlite:///db/logs${i}.db"
    HEALTH_DB="sqlite:///db/health${i}.db"
    SANDBOX_DB="sqlite:///db/sandbox${i}.db"
    HISTORIFY_DB="db/historify${i}.duckdb"

    # Session/CSRF cookie names
    SESSION_COOKIE="session${i}"
    CSRF_COOKIE="csrf_token${i}"

    # Update .env file
    # IMPORTANT: Order matters! Update broker and domain BEFORE ports

    # 1. Replace broker placeholder first
    sudo sed -i "s|<broker>|$BROKER|g" "$ENV_FILE"

    # 2. Replace domain URLs (before port changes)
    sudo sed -i "s|http://127.0.0.1:5000|https://$DOMAIN|g" "$ENV_FILE"
    # Explicitly set HOST_SERVER in case the default value didn't match
    sudo sed -i "s|HOST_SERVER = '.*'|HOST_SERVER = 'https://$DOMAIN'|g" "$ENV_FILE"
    sudo sed -i "s|CORS_ALLOWED_ORIGINS = '.*'|CORS_ALLOWED_ORIGINS = 'https://$DOMAIN'|g" "$ENV_FILE"

    # 3. Update ports (these stay as localhost for internal communication)
    sudo sed -i "s|FLASK_PORT='[0-9]*'|FLASK_PORT='$FLASK_PORT'|g" "$ENV_FILE"
    sudo sed -i "s|WEBSOCKET_PORT='[0-9]*'|WEBSOCKET_PORT='$WS_PORT'|g" "$ENV_FILE"
    sudo sed -i "s|ZMQ_PORT='[0-9]*'|ZMQ_PORT='$ZMQ_PORT'|g" "$ENV_FILE"

    # 4. Update WebSocket URL for production (secure WebSocket through nginx)
    sudo sed -i "s|WEBSOCKET_URL='.*'|WEBSOCKET_URL='wss://$DOMAIN/ws'|g" "$ENV_FILE"

    # 5. Host bindings intentionally left at 127.0.0.1 (the .sample.env default):
    #    nginx on this host reverse-proxies /ws -> 127.0.0.1:WEBSOCKET_PORT, and
    #    ZMQ is an internal message bus that must never be exposed publicly.

    # 6. Update API credentials
    sudo sed -i "s|YOUR_BROKER_API_KEY|$API_KEY|g" "$ENV_FILE"
    sudo sed -i "s|YOUR_BROKER_API_SECRET|$API_SECRET|g" "$ENV_FILE"

    # 7. Update security keys
    sudo sed -i "s|OPENALGO_PLACEHOLDER_APP_KEY_REGENERATE_BEFORE_USE|$APP_KEY|g" "$ENV_FILE"
    sudo sed -i "s|OPENALGO_PLACEHOLDER_API_KEY_PEPPER_REGENERATE_BEFORE_USE|$API_KEY_PEPPER|g" "$ENV_FILE"

    # Each instance runs gunicorn behind nginx (Unix socket bind). Trust the
    # proxy's X-Forwarded-For / X-Real-IP for IP-based features.
    sudo sed -i "s|TRUST_PROXY_HEADERS = 'FALSE'|TRUST_PROXY_HEADERS = 'TRUE'|g" "$ENV_FILE"

    # 8. Update database paths (unique per instance - ALL 6 databases)
    sudo sed -i "s|DATABASE_URL = '.*'|DATABASE_URL = '$DB_PATH'|g" "$ENV_FILE"
    sudo sed -i "s|LATENCY_DATABASE_URL = '.*'|LATENCY_DATABASE_URL = '$LATENCY_DB'|g" "$ENV_FILE"
    sudo sed -i "s|LOGS_DATABASE_URL = '.*'|LOGS_DATABASE_URL = '$LOGS_DB'|g" "$ENV_FILE"
    sudo sed -i "s|HEALTH_DATABASE_URL = '.*'|HEALTH_DATABASE_URL = '$HEALTH_DB'|g" "$ENV_FILE"
    sudo sed -i "s|SANDBOX_DATABASE_URL = '.*'|SANDBOX_DATABASE_URL = '$SANDBOX_DB'|g" "$ENV_FILE"
    sudo sed -i "s|HISTORIFY_DATABASE_URL = '.*'|HISTORIFY_DATABASE_URL = '$HISTORIFY_DB'|g" "$ENV_FILE"

    # 9. Update session/CSRF cookies (CRITICAL for instance isolation)
    sudo sed -i "s|SESSION_COOKIE_NAME = '.*'|SESSION_COOKIE_NAME = '$SESSION_COOKIE'|g" "$ENV_FILE"
    sudo sed -i "s|CSRF_COOKIE_NAME = '.*'|CSRF_COOKIE_NAME = '$CSRF_COOKIE'|g" "$ENV_FILE"

    # 10. Update Flask host IP binding (internal only)
    sudo sed -i "s|FLASK_HOST_IP='.*'|FLASK_HOST_IP='127.0.0.1'|g" "$ENV_FILE"

    # 11. Enable Remote MCP if the operator opted in for this instance.
    # Same-domain mode: /mcp and /oauth/* are served from the same nginx
    # vhost as the dashboard. Other MCP_* keys (auto-approve, write scope,
    # CORS allowlist) inherit their defaults from .sample.env — flip them
    # later in the per-instance .env if you want stricter behavior.
    if [ "$ENABLE_REMOTE_MCP" = "true" ]; then
        sudo sed -i "s|MCP_HTTP_ENABLED = 'False'|MCP_HTTP_ENABLED = 'True'|g" "$ENV_FILE"
        sudo sed -i "s|MCP_PUBLIC_URL = ''|MCP_PUBLIC_URL = 'https://$DOMAIN'|g" "$ENV_FILE"
    fi

    # XTS broker credentials
    if [ "$IS_XTS_INSTANCE" = "true" ]; then
        sudo sed -i "s|YOUR_BROKER_MARKET_API_KEY|$API_KEY_MARKET|g" "$ENV_FILE"
        sudo sed -i "s|YOUR_BROKER_MARKET_API_SECRET|$API_SECRET_MARKET|g" "$ENV_FILE"
    fi

    # Set permissions
    log_message "Setting permissions..." "$BLUE"
    sudo mkdir -p "$INSTANCE_DIR/db"
    sudo mkdir -p "$INSTANCE_DIR/tmp/numba_cache"
    sudo mkdir -p "$INSTANCE_DIR/tmp/matplotlib"
    # Create directories for Python strategy feature
    sudo mkdir -p "$INSTANCE_DIR/strategies/scripts"
    sudo mkdir -p "$INSTANCE_DIR/strategies/examples"
    sudo mkdir -p "$INSTANCE_DIR/log/strategies"
    sudo mkdir -p "$INSTANCE_DIR/keys"
    sudo chown -R www-data:www-data "$INSTANCE_DIR"
    sudo chmod -R 755 "$INSTANCE_DIR"
    # Set more restrictive permissions for sensitive directories
    sudo chmod 700 "$INSTANCE_DIR/keys"
    # Restrict .env to the service account only — contains APP_KEY, API_KEY_PEPPER,
    # broker API credentials. The recursive chmod 755 above would otherwise leave
    # it world-readable on shared multi-tenant boxes.
    sudo chmod 600 "$ENV_FILE"
    [ -S "$SOCKET_FILE" ] && sudo rm -f "$SOCKET_FILE"

    # Configure Nginx (initial for SSL)
    log_message "Configuring Nginx for SSL..." "$BLUE"
    sudo tee /etc/nginx/sites-available/$DOMAIN > /dev/null << EOL
server {
    listen 80;
    listen [::]:80;
    server_name $DOMAIN;
    root /var/www/html;

    location / {
        try_files \$uri \$uri/ =404;
    }
}
EOL

    sudo ln -sf /etc/nginx/sites-available/$DOMAIN /etc/nginx/sites-enabled/

    # Remove default on first instance
    if [ $i -eq 1 ]; then
        sudo rm -f /etc/nginx/sites-enabled/default
    fi

    # Reload Nginx
    sudo nginx -t && sudo systemctl reload nginx
    check_status "Failed to reload Nginx"

    # Obtain SSL certificate
    log_message "Obtaining SSL certificate for $DOMAIN..." "$BLUE"
    sudo certbot --nginx -d $DOMAIN --non-interactive --agree-tos --email admin@${DOMAIN#*.}
    check_status "Failed to obtain SSL certificate"

    # Configure final Nginx with SSL and WebSocket
    log_message "Configuring final Nginx setup..." "$BLUE"
    sudo tee /etc/nginx/sites-available/$DOMAIN > /dev/null << EOL
server {
    listen 80;
    listen [::]:80;
    server_name $DOMAIN;

    # WebSocket redirect exceptions
    location = /ws {
        return 301 https://\$host\$request_uri;
    }

    location /ws/ {
        return 301 https://\$host\$request_uri;
    }

    location / {
        return 301 https://\$host\$request_uri;
    }
}

server {
    listen 443 ssl;
    listen [::]:443 ssl;

    server_name $DOMAIN;

    ssl_certificate /etc/letsencrypt/live/$DOMAIN/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/$DOMAIN/privkey.pem;

    # SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers on;
    ssl_ciphers EECDH+AESGCM:EDH+AESGCM;
    ssl_ecdh_curve secp384r1;
    ssl_session_timeout 10m;
    ssl_session_cache shared:SSL:10m;
    ssl_session_tickets off;
    ssl_stapling on;
    ssl_stapling_verify on;

    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=63072000" always;

    # WebSocket endpoints
    location = /ws {
        proxy_pass http://127.0.0.1:$WS_PORT;
        proxy_http_version 1.1;
        proxy_read_timeout 86400s;
        proxy_send_timeout 86400s;
        proxy_buffering off;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    location /ws/ {
        proxy_pass http://127.0.0.1:$WS_PORT/;
        proxy_http_version 1.1;
        proxy_read_timeout 86400s;
        proxy_send_timeout 86400s;
        proxy_buffering off;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    # Socket.IO (Flask-SocketIO real-time events)
    location /socket.io/ {
        proxy_pass http://unix:$SOCKET_FILE;
        proxy_http_version 1.1;
        proxy_read_timeout 86400s;
        proxy_send_timeout 86400s;
        proxy_buffering off;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    # Main app via Unix socket
    location / {
        proxy_pass http://unix:$SOCKET_FILE;
        proxy_http_version 1.1;

        # Extended timeouts for broker authentication (cold start can take 60-90s)
        proxy_read_timeout 300s;
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;

        # Increased buffer sizes for large headers (auth tokens, session cookies)
        proxy_buffer_size 128k;
        proxy_buffers 4 256k;
        proxy_busy_buffers_size 256k;

        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_redirect off;
    }
}
EOL

    sudo nginx -t
    check_status "Failed to validate Nginx config"

    # Create systemd service
    log_message "Creating systemd service..." "$BLUE"
    sudo tee /etc/systemd/system/$SERVICE_NAME.service > /dev/null << EOL
[Unit]
Description=OpenAlgo Instance $i ($DOMAIN - $BROKER)
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=$INSTANCE_DIR
# Set HOME so Kaleido/choreographer can write temp files for Telegram /chart.
# Kaleido 1.x creates temp dirs in Path.home() (not TMPDIR); the default
# www-data home /var/www/ is typically root-owned and not writable.
Environment="HOME=$INSTANCE_DIR/tmp"
# Environment variables for numba/scipy support
Environment="TMPDIR=$INSTANCE_DIR/tmp"
Environment="NUMBA_CACHE_DIR=$INSTANCE_DIR/tmp/numba_cache"
Environment="LLVMLITE_TMPDIR=$INSTANCE_DIR/tmp"
Environment="MPLCONFIGDIR=$INSTANCE_DIR/tmp/matplotlib"
# Limit OpenBLAS/NumPy threads to prevent RLIMIT_NPROC exhaustion
# See: https://github.com/marketcalls/openalgo/issues/822
Environment="OPENBLAS_NUM_THREADS=2"
Environment="OMP_NUM_THREADS=2"
Environment="MKL_NUM_THREADS=2"
Environment="NUMEXPR_NUM_THREADS=2"
Environment="NUMBA_NUM_THREADS=2"
ExecStart=/bin/bash -c 'source $VENV_PATH/bin/activate && $VENV_PATH/bin/gunicorn \\
    --worker-class eventlet \\
    -w 1 \\
    --bind unix:$SOCKET_FILE \\
    --timeout 300 \\
    --log-level info \\
    app:app'
Restart=always
RestartSec=5
TimeoutSec=300

[Install]
WantedBy=multi-user.target
EOL

    # Enable and start service
    log_message "Starting service..." "$BLUE"
    sudo systemctl daemon-reload
    sudo systemctl enable $SERVICE_NAME
    sudo systemctl start $SERVICE_NAME
    check_status "Failed to start service"

    log_message "✅ Instance $i installed successfully!" "$GREEN"
    log_message "   URL: https://$DOMAIN" "$BLUE"
    log_message "   Flask:$FLASK_PORT | WS:$WS_PORT | ZMQ:$ZMQ_PORT" "$BLUE"
    log_message "   Service: $SERVICE_NAME" "$BLUE"
    if [ "$ENABLE_REMOTE_MCP" = "true" ]; then
        log_message "   Remote MCP: Enabled at https://$DOMAIN/mcp" "$BLUE"
    else
        log_message "   Remote MCP: Disabled" "$BLUE"
    fi
done

# Final Nginx reload
log_message "\nReloading Nginx..." "$BLUE"
sudo systemctl reload nginx

# Summary
log_message "\n╔════════════════════════════════════════════════════════╗" "$GREEN"
log_message "║          MULTI-INSTANCE INSTALLATION COMPLETE          ║" "$GREEN"
log_message "╚════════════════════════════════════════════════════════╝" "$GREEN"

log_message "\n📋 INSTANCE SUMMARY:" "$YELLOW"
for ((i=1; i<=INSTANCES; i++)); do
    idx=$((i-1))
    log_message "\nInstance $i:" "$BLUE"
    log_message "  Domain: https://${DOMAINS[$idx]}" "$GREEN"
    log_message "  Broker: ${BROKERS[$idx]}" "$BLUE"
    log_message "  Service: openalgo$i" "$BLUE"
    log_message "  Directory: $BASE_DIR/openalgo$i" "$BLUE"
    if [ "${MCP_ENABLED_LIST[$idx]}" = "true" ]; then
        log_message "  Remote MCP: Enabled at https://${DOMAINS[$idx]}/mcp" "$BLUE"
    else
        log_message "  Remote MCP: Disabled" "$BLUE"
    fi
done

log_message "\n📚 USEFUL COMMANDS:" "$YELLOW"
log_message "View all services: systemctl list-units 'openalgo*'" "$BLUE"
log_message "Restart instance: sudo systemctl restart openalgo<N>" "$BLUE"
log_message "View logs: sudo journalctl -u openalgo<N> -f" "$BLUE"
log_message "Check status: sudo systemctl status openalgo<N>" "$BLUE"

log_message "\n📝 Installation log saved to: $LOG_FILE" "$BLUE"
log_message "\n🎉 All instances are ready to use!" "$GREEN"

```


---

# FILE: install\install.sh

```sh
#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# openalgo Installation Banner
echo -e "${BLUE}"
echo "  ██████╗ ██████╗ ███████╗███╗   ██╗ █████╗ ██╗      ██████╗  ██████╗ "
echo " ██╔═══██╗██╔══██╗██╔════╝████╗  ██║██╔══██╗██║     ██╔════╝ ██╔═══██╗"
echo " ██║   ██║██████╔╝███████╗██╔██╗ ██║███████║██║     ██║  ███╗██║   ██║"
echo " ██║   ██║██╔═══╝ ██╔══╝  ██║╚██╗██║██╔══██║██║     ██║   ██║██║   ██║"
echo " ╚██████╔╝██╗     ███████╗██║ ╚████║██║  ██║███████╗╚██████╔╝╚██████╔╝"
echo "  ╚═════╝ ╚═╝     ╚══════╝╚═╝  ╚═══╝╚═╝  ╚═╝╚══════╝ ╚═════╝  ╚═════╝ "      
echo "                                                                        "
echo -e "${NC}"

# OpenAlgo Installation and Configuration Script



# Create logs directory if it doesn't exist
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
LOGS_DIR="$SCRIPT_DIR/logs"
mkdir -p "$LOGS_DIR"

# Generate unique log file name for this deployment
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_FILE="$LOGS_DIR/install_${TIMESTAMP}.log"

# Function to log messages to both console and log file
log_message() {
    local message="$1"
    local color="$2"
    echo -e "${color}${message}${NC}" | tee -a "$LOG_FILE"
}

# Function to check if command was successful
check_status() {
    if [ $? -ne 0 ]; then
        log_message "Error: $1" "$RED"
        exit 1
    fi
}

# Function to check current timezone
check_timezone() {
    current_tz=$(timedatectl | grep "Time zone" | awk '{print $3}')
    log_message "Current timezone: $current_tz" "$BLUE"
    
    if [[ "$current_tz" == "Asia/Kolkata" ]]; then
        log_message "Server is already set to IST timezone." "$GREEN"
        return 0
    fi
    
    log_message "Server is not set to IST timezone." "$YELLOW"
    read -p "Would you like to change the timezone to IST? (y/n): " change_tz
    if [[ $change_tz =~ ^[Yy]$ ]]; then
        log_message "Changing timezone to IST..." "$BLUE"
        sudo timedatectl set-timezone Asia/Kolkata
        check_status "Failed to change timezone"
        log_message "Timezone successfully changed to IST" "$GREEN"
    else
        log_message "Keeping current timezone: $current_tz" "$YELLOW"
    fi
}

# Function to wait for dpkg lock to be released (Ubuntu/Debian)
wait_for_dpkg_lock() {
    local max_wait=300  # 5 minutes max wait
    local waited=0

    while sudo fuser /var/lib/dpkg/lock-frontend >/dev/null 2>&1 || \
          sudo fuser /var/lib/dpkg/lock >/dev/null 2>&1 || \
          sudo fuser /var/lib/apt/lists/lock >/dev/null 2>&1; do

        if [ $waited -eq 0 ]; then
            log_message "Package manager is locked (unattended-upgrades running)" "$YELLOW"
            log_message "Waiting for it to complete... (max 5 minutes)" "$YELLOW"
        fi

        if [ $waited -ge $max_wait ]; then
            log_message "Timeout waiting for package manager lock" "$RED"
            log_message "Please run: sudo killall unattended-upgr && sudo rm /var/lib/dpkg/lock*" "$YELLOW"
            exit 1
        fi

        printf "."
        sleep 5
        waited=$((waited + 5))
    done

    if [ $waited -gt 0 ]; then
        echo ""
        log_message "Package manager is now available" "$GREEN"
    fi
}

# Function to generate random hex string
generate_hex() {
    $PYTHON_CMD -c "import secrets; print(secrets.token_hex(32))"
}




# Function to validate broker name
validate_broker() {
    local broker=$1

    local valid_brokers="fivepaisa,fivepaisaxts,aliceblue,angel,compositedge,definedge,deltaexchange,dhan,dhan_sandbox,firstock,flattrade,fyers,groww,ibulls,iifl,iiflcapital,indmoney,jainamxts,kotak,motilal,mstock,nubra,paytm,pocketful,rmoney,samco,shoonya,tradejini,upstox,wisdom,zebu,zerodha"

    if [[ ",$valid_brokers," == *",$broker,"* ]]; then
        return 0
    else
        return 1
    fi
}

# Function to check if broker is XTS based
is_xts_broker() {
    local broker=$1
    local xts_brokers="fivepaisaxts,compositedge,ibulls,iifl,jainamxts,rmoney,wisdom"
    if [[ ",$xts_brokers," == *",$broker,"* ]]; then
        return 0
    else
        return 1
    fi
}

# Function to check if broker is crypto based (24/7 markets, no auto-logout)
# Uses space-delimited boundary matching for exact broker ID checks
is_crypto_broker() {
    local broker=$1
    local crypto_brokers=" deltaexchange "
    if [[ $crypto_brokers == *" $broker "* ]]; then
        return 0
    else
        return 1
    fi
}

# Function to check and handle existing files/directories
handle_existing() {
    local path=$1
    local type=$2
    local name=$3

    if [ -e "$path" ]; then
        log_message "Warning: $name already exists at $path" "$YELLOW"
        read -p "Would you like to backup the existing $type? (y/n): " backup_choice
        if [[ $backup_choice =~ ^[Yy]$ ]]; then
            backup_path="${path}_backup_$(date +%Y%m%d_%H%M%S)"
            log_message "Creating backup at $backup_path" "$BLUE"
            sudo mv "$path" "$backup_path"
            check_status "Failed to create backup of $name"
            return 0
        else
            read -p "Would you like to remove the existing $type? (y/n): " remove_choice
            if [[ $remove_choice =~ ^[Yy]$ ]]; then
                log_message "Removing existing $type..." "$BLUE"
                if [ -d "$path" ]; then
                    sudo rm -rf "$path"
                else
                    sudo rm -f "$path"
                fi
                check_status "Failed to remove existing $type"
                return 0
            else
                log_message "Installation cannot proceed without handling existing $type" "$RED"
                exit 1
            fi
        fi
    fi
    return 0
}

# Function to check and configure swap memory
check_and_configure_swap() {
    # Get total RAM in MB
    TOTAL_RAM_KB=$(grep MemTotal /proc/meminfo | awk '{print $2}')
    TOTAL_RAM_MB=$((TOTAL_RAM_KB / 1024))
    TOTAL_RAM_GB=$((TOTAL_RAM_MB / 1024))
    
    log_message "System RAM: ${TOTAL_RAM_MB}MB (${TOTAL_RAM_GB}GB)" "$BLUE"
    
    # Check if RAM is less than 2GB
    if [ $TOTAL_RAM_MB -lt 2048 ]; then
        log_message "System has less than 2GB RAM. Checking swap configuration..." "$YELLOW"
        
        # Check current swap
        SWAP_TOTAL=$(free -m | grep Swap | awk '{print $2}')
        log_message "Current swap: ${SWAP_TOTAL}MB" "$BLUE"
        
        if [ $SWAP_TOTAL -lt 3072 ]; then
            log_message "Insufficient swap memory. Creating 3GB swap file..." "$YELLOW"
            
            # Check available disk space
            AVAILABLE_SPACE=$(df / | tail -1 | awk '{print $4}')
            REQUIRED_SPACE=3145728  # 3GB in KB
            
            if [ $AVAILABLE_SPACE -lt $REQUIRED_SPACE ]; then
                log_message "Error: Not enough disk space for swap file" "$RED"
                log_message "Available: ${AVAILABLE_SPACE}KB, Required: ${REQUIRED_SPACE}KB" "$RED"
                exit 1
            fi
            
            # Create swap file
            log_message "Creating 3GB swap file at /swapfile..." "$BLUE"
            sudo fallocate -l 3G /swapfile
            if [ $? -ne 0 ]; then
                # Fallback to dd if fallocate fails
                log_message "fallocate failed, using dd instead..." "$YELLOW"
                sudo dd if=/dev/zero of=/swapfile bs=1M count=3072 status=progress
            fi
            check_status "Failed to create swap file"
            
            # Set permissions
            sudo chmod 600 /swapfile
            check_status "Failed to set swap file permissions"
            
            # Setup swap
            sudo mkswap /swapfile
            check_status "Failed to setup swap"
            
            # Enable swap
            sudo swapon /swapfile
            check_status "Failed to enable swap"
            
            # Make swap permanent
            if ! grep -q "/swapfile" /etc/fstab; then
                echo "/swapfile none swap sw 0 0" | sudo tee -a /etc/fstab
                log_message "Swap file added to /etc/fstab for persistence" "$GREEN"
            fi
            
            # Verify swap is active
            NEW_SWAP=$(free -m | grep Swap | awk '{print $2}')
            log_message "Swap configured successfully. Total swap: ${NEW_SWAP}MB" "$GREEN"
            
            # Configure swappiness for better performance
            sudo sysctl vm.swappiness=10
            echo "vm.swappiness=10" | sudo tee -a /etc/sysctl.conf
            log_message "Swappiness set to 10 for better performance" "$GREEN"
        else
            log_message "Sufficient swap already exists: ${SWAP_TOTAL}MB" "$GREEN"
        fi
    else
        log_message "System has sufficient RAM (${TOTAL_RAM_GB}GB)" "$GREEN"
        
        # Still check swap for optimal performance
        SWAP_TOTAL=$(free -m | grep Swap | awk '{print $2}')
        if [ $SWAP_TOTAL -eq 0 ]; then
            log_message "No swap configured. Consider adding swap for optimal performance." "$YELLOW"
        else
            log_message "Swap configured: ${SWAP_TOTAL}MB" "$GREEN"
        fi
    fi
}

# Start logging
log_message "Starting OpenAlgo installation log at: $LOG_FILE" "$BLUE"
log_message "----------------------------------------" "$BLUE"

# Detect OS type and version
OS_TYPE=$(grep -w "ID" /etc/os-release | cut -d "=" -f 2 | tr -d '"')

# Handle OS variants - map to base distributions
case "$OS_TYPE" in
    "pop")
        OS_TYPE="ubuntu"
        log_message "Detected Pop!_OS, using Ubuntu packages" "$BLUE"
        ;;
    "linuxmint")
        OS_TYPE="ubuntu"
        log_message "Detected Linux Mint, using Ubuntu packages" "$BLUE"
        ;;
    "zorin")
        OS_TYPE="ubuntu"
        log_message "Detected Zorin OS, using Ubuntu packages" "$BLUE"
        ;;
    "manjaro" | "manjaro-arm" | "endeavouros" | "cachyos")
        OS_TYPE="arch"
        log_message "Detected $OS_TYPE, using Arch Linux packages" "$BLUE"
        ;;
    "rocky" | "almalinux" | "ol")
        OS_TYPE="rhel"
        log_message "Detected $OS_TYPE, using RHEL-compatible packages" "$BLUE"
        ;;
esac

# Get OS version
if [ "$OS_TYPE" = "arch" ]; then
    OS_VERSION="rolling"
else
    OS_VERSION=$(grep -w "VERSION_ID" /etc/os-release | cut -d "=" -f 2 | tr -d '"')
fi

# Validate supported OS
case "$OS_TYPE" in
    arch | ubuntu | debian | raspbian | centos | fedora | rhel | rocky | almalinux | amzn)
        log_message "Detected OS: $OS_TYPE $OS_VERSION" "$GREEN"
        ;;
    *)
        log_message "Error: Unsupported operating system: $OS_TYPE" "$RED"
        log_message "Supported: Ubuntu, Debian, Raspbian, CentOS, Fedora, RHEL, Rocky, AlmaLinux, Amazon Linux, Arch Linux" "$YELLOW"
        exit 1
        ;;
esac

# Detect web server user and Python command based on OS
case "$OS_TYPE" in
    ubuntu | debian | raspbian)
        WEB_USER="www-data"
        WEB_GROUP="www-data"
        PYTHON_CMD="python3"
        ;;
    centos | fedora | rhel | amzn)
        WEB_USER="nginx"
        WEB_GROUP="nginx"
        PYTHON_CMD="python3"
        ;;
    arch)
        WEB_USER="http"
        WEB_GROUP="http"
        PYTHON_CMD="python"
        ;;
esac

log_message "Web server user: $WEB_USER:$WEB_GROUP" "$BLUE"
log_message "Python command: $PYTHON_CMD" "$BLUE"

# Check system requirements (RAM and swap)
log_message "Checking system requirements..." "$BLUE"
check_and_configure_swap

# Check timezone before proceeding with installation
check_timezone

# Collect installation parameters
log_message "OpenAlgo Installation Configuration" "$BLUE"
log_message "----------------------------------------" "$BLUE"

# Get domain name
while true; do
    read -p "Enter your domain name (e.g., yourdomain.com or sub.yourdomain.com): " DOMAIN
    if [ -z "$DOMAIN" ]; then
        log_message "Error: Domain name is required" "$RED"
        continue
    fi
    # Domain validation that accepts subdomains
    if [[ ! $DOMAIN =~ ^[a-zA-Z0-9]([a-zA-Z0-9-]*[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9-]*[a-zA-Z0-9])?)*\.[a-zA-Z]{2,}$ ]]; then
        log_message "Error: Invalid domain format. Please enter a valid domain name" "$RED"
        continue
    fi

    # Check if it's a subdomain
    if [[ $DOMAIN =~ ^[^.]+\.[^.]+\.[^.]+$ ]]; then
        IS_SUBDOMAIN=true
    else
        IS_SUBDOMAIN=false
    fi
    break
done

# Get broker name
while true; do

    log_message "\nValid brokers: fivepaisa,fivepaisaxts,aliceblue,angel,compositedge,definedge,deltaexchange,dhan,dhan_sandbox,firstock,flattrade,fyers,groww,ibulls,iifl,iiflcapital,indmoney,jainamxts,kotak,motilal,mstock,nubra,paytm,pocketful,rmoney,samco,shoonya,tradejini,upstox,wisdom,zebu,zerodha" "$BLUE"

    read -p "Enter your broker name: " BROKER_NAME
    if validate_broker "$BROKER_NAME"; then
        break
    else
        log_message "Invalid broker name. Please choose from the list above." "$RED"
    fi
done

# Show redirect URL for broker setup
log_message "\nRedirect URL for broker developer portal:" "$YELLOW"
log_message "https://$DOMAIN/$BROKER_NAME/callback" "$GREEN"
log_message "\nPlease use this URL in your broker's developer portal to generate API credentials." "$BLUE"
log_message "Once you have the credentials, you can proceed with the installation." "$BLUE"
echo ""

# Get broker API credentials
read -p "Enter your broker API key: " BROKER_API_KEY
read -p "Enter your broker API secret: " BROKER_API_SECRET

if [ -z "$BROKER_API_KEY" ] || [ -z "$BROKER_API_SECRET" ]; then
    log_message "Error: Broker API credentials are required" "$RED"
    exit 1
fi

# Check if the broker is XTS-based and ask for additional credentials if needed
BROKER_API_KEY_MARKET=""
BROKER_API_SECRET_MARKET=""
if is_xts_broker "$BROKER_NAME"; then
    log_message "\nThis broker ($BROKER_NAME) is XTS API-based and requires additional market data credentials." "$YELLOW"
    read -p "Enter your broker market data API key: " BROKER_API_KEY_MARKET
    read -p "Enter your broker market data API secret: " BROKER_API_SECRET_MARKET
    
    if [ -z "$BROKER_API_KEY_MARKET" ] || [ -z "$BROKER_API_SECRET_MARKET" ]; then
        log_message "Error: Market data API credentials are required for XTS-based brokers" "$RED"
        exit 1
    fi
fi

# Check if the broker is crypto-based and disable auto-logout
DISABLE_SESSION_EXPIRY="false"
if is_crypto_broker "$BROKER_NAME"; then
    log_message "\nThis broker ($BROKER_NAME) operates on 24/7 crypto markets." "$YELLOW"
    log_message "Auto-logout (session expiry at 3 AM IST) will be disabled." "$GREEN"
    DISABLE_SESSION_EXPIRY="true"
fi

# Optional: Remote MCP for hosted AI clients (Claude.ai, ChatGPT).
# Same-domain mode — /mcp and /oauth/* are served from the same nginx
# vhost as the dashboard, so the existing reverse-proxy config covers it.
# Local stdio MCP (Claude Desktop / Cursor / Windsurf) works regardless.
log_message "\nRemote MCP lets hosted AI clients (Claude.ai, ChatGPT) connect to OpenAlgo over HTTPS." "$BLUE"
log_message "Skip this if you only use the local MCP server with Claude Desktop / Cursor." "$YELLOW"
read -p "Enable Remote MCP? (y/N): " enable_mcp_input
ENABLE_REMOTE_MCP="false"
if [[ $enable_mcp_input =~ ^[Yy]$ ]]; then
    ENABLE_REMOTE_MCP="true"
    log_message "Remote MCP will be enabled at https://$DOMAIN/mcp" "$GREEN"
fi

# Generate random keys
APP_KEY=$(generate_hex)
API_KEY_PEPPER=$(generate_hex)

# Installation paths — single deployment per server. For 2+ deployments
# side-by-side use install/install-multi.sh (different scheme).
#
#   App, venv, socket, .env all live under /var/python/openalgo
#   systemd unit:  openalgo.service
#   nginx vhost:   openalgo.conf
DEPLOY_NAME="openalgo"
OPENALGO_PATH="/var/python/openalgo"
BASE_PATH="$OPENALGO_PATH"
VENV_PATH="$OPENALGO_PATH/.venv"
SOCKET_PATH="$OPENALGO_PATH"
SOCKET_FILE="$SOCKET_PATH/openalgo.sock"
SERVICE_NAME="openalgo"

# Set Nginx configuration paths based on OS
case "$OS_TYPE" in
    ubuntu | debian | raspbian)
        NGINX_AVAILABLE="/etc/nginx/sites-available"
        NGINX_ENABLED="/etc/nginx/sites-enabled"
        NGINX_CONFIG_MODE="sites"
        ;;
    centos | fedora | rhel | amzn | arch)
        NGINX_AVAILABLE="/etc/nginx/conf.d"
        NGINX_ENABLED="/etc/nginx/conf.d"
        NGINX_CONFIG_MODE="confd"
        # Create conf.d directory if it doesn't exist (Arch Linux)
        sudo mkdir -p "$NGINX_AVAILABLE"
        ;;
esac
NGINX_CONFIG_FILE="$NGINX_AVAILABLE/openalgo.conf"

log_message "\nStarting OpenAlgo installation for $DEPLOY_NAME..." "$YELLOW"

# Update system packages
log_message "\nUpdating system packages..." "$BLUE"
case "$OS_TYPE" in
    ubuntu | debian | raspbian)
        # Wait for any running package manager operations to complete
        wait_for_dpkg_lock
        sudo apt-get update && sudo apt-get upgrade -y
        check_status "Failed to update system packages"
        ;;
    centos | fedora | rhel | amzn)
        if ! command -v dnf >/dev/null 2>&1; then
            sudo yum update -y
        else
            sudo dnf update -y
        fi
        check_status "Failed to update system packages"
        ;;
    arch)
        sudo pacman -Syu --noconfirm
        check_status "Failed to update system packages"
        ;;
esac

# Install required packages including Certbot
log_message "\nInstalling required packages..." "$BLUE"
case "$OS_TYPE" in
    ubuntu | debian | raspbian)
        # Wait for any running package manager operations to complete
        wait_for_dpkg_lock
        sudo apt-get install -y python3 python3-venv python3-pip nginx git software-properties-common \
            libopenblas0 libgomp1 libgfortran5
        # Try to install python3-full if available (Ubuntu 23.04+)
        sudo apt-get install -y python3-full 2>/dev/null || log_message "python3-full not available, skipping" "$YELLOW"
        # Try to install snapd, but don't fail if unavailable
        sudo apt-get install -y snapd 2>/dev/null || log_message "snapd not available, will use pip for uv installation" "$YELLOW"
        check_status "Failed to install required packages"
        # Install Chromium for Kaleido/Plotly static chart rendering (Telegram /chart command).
        # Kaleido 1.x ships no bundled browser; it drives a system Chromium via choreographer.
        # Debian/Raspbian have 'chromium' in main. Ubuntu 19.10+ renamed it to 'chromium-browser'
        # which is a transitional package that installs the Chromium snap (works headless).
        # Non-fatal — if nothing sticks we just warn; the rest of openalgo still installs fine.
        log_message "\nInstalling Chromium for Telegram /chart rendering..." "$BLUE"
        if sudo apt-get install -y chromium fonts-liberation 2>/dev/null; then
            log_message "Installed chromium (Debian package)" "$GREEN"
        elif sudo apt-get install -y chromium-browser fonts-liberation 2>/dev/null; then
            log_message "Installed chromium-browser (Ubuntu transitional/snap)" "$GREEN"
        else
            log_message "Chromium install failed - Telegram /chart will not render charts" "$YELLOW"
            log_message "You can install it manually later: sudo snap install chromium" "$YELLOW"
        fi
        ;;
    centos | fedora | rhel | amzn)
        if ! command -v dnf >/dev/null 2>&1; then
            sudo yum install -y python3 python3-pip nginx git epel-release \
                openblas-devel gcc-gfortran libgomp
            # Install SELinux management tools for RHEL-based systems
            sudo yum install -y policycoreutils-python-utils 2>/dev/null || log_message "SELinux tools already installed" "$YELLOW"
            # Try to install snapd, but don't fail if unavailable (we use pip for uv anyway)
            sudo yum install -y snapd 2>/dev/null || log_message "snapd not available, will use pip for uv installation" "$YELLOW"
        else
            # Install EPEL repository first for access to additional packages
            sudo dnf install -y epel-release 2>/dev/null || log_message "EPEL repository already installed or not available" "$YELLOW"
            sudo dnf install -y python3 python3-pip nginx git \
                openblas-devel gcc-gfortran libgomp
            # Install SELinux management tools for RHEL-based systems
            sudo dnf install -y policycoreutils-python-utils 2>/dev/null || log_message "SELinux tools already installed" "$YELLOW"
            # Try to install snapd, but don't fail if unavailable (we use pip for uv anyway)
            sudo dnf install -y snapd 2>/dev/null || log_message "snapd not available, will use pip for uv installation" "$YELLOW"
        fi
        check_status "Failed to install required packages"
        # Install Chromium for Kaleido/Plotly static chart rendering (Telegram /chart command).
        # Available in EPEL for RHEL/CentOS, main repo for Fedora. Amazon Linux 2023 does
        # not ship Chromium — in that case the install falls through and /chart is disabled
        # until the operator installs Chrome/Chromium manually. Non-fatal.
        log_message "\nInstalling Chromium for Telegram /chart rendering..." "$BLUE"
        if command -v dnf >/dev/null 2>&1; then
            if sudo dnf install -y chromium liberation-fonts 2>/dev/null; then
                log_message "Installed chromium via dnf" "$GREEN"
            else
                log_message "Chromium not available via dnf - Telegram /chart will not render charts" "$YELLOW"
                log_message "For Amazon Linux 2023, install google-chrome-stable manually" "$YELLOW"
            fi
        else
            if sudo yum install -y chromium liberation-fonts 2>/dev/null; then
                log_message "Installed chromium via yum" "$GREEN"
            else
                log_message "Chromium not available via yum - Telegram /chart will not render charts" "$YELLOW"
                log_message "Make sure EPEL is enabled, or install google-chrome-stable manually" "$YELLOW"
            fi
        fi
        # Enable and start snapd if it was successfully installed
        if command -v snap >/dev/null 2>&1; then
            sudo systemctl enable --now snapd.socket
        fi
        ;;
    arch)
        sudo pacman -Sy --noconfirm --needed python python-pip nginx git \
            openblas gcc-fortran
        # Try to install snapd, but don't fail if unavailable (we use pip for uv anyway)
        sudo pacman -Sy --noconfirm --needed snapd 2>/dev/null || log_message "snapd not available, will use pip for uv installation" "$YELLOW"
        check_status "Failed to install required packages"
        # Install Chromium for Kaleido/Plotly static chart rendering (Telegram /chart command).
        # Non-fatal — if install fails we warn and continue.
        log_message "\nInstalling Chromium for Telegram /chart rendering..." "$BLUE"
        if sudo pacman -S --noconfirm --needed chromium ttf-liberation 2>/dev/null; then
            log_message "Installed chromium via pacman" "$GREEN"
        else
            log_message "Chromium install failed - Telegram /chart will not render charts" "$YELLOW"
        fi
        # Enable and start snapd if it was successfully installed
        if command -v snap >/dev/null 2>&1; then
            sudo systemctl enable --now snapd.socket
        fi
        ;;
esac

# Install uv package installer
log_message "\nInstalling uv package installer..." "$BLUE"
case "$OS_TYPE" in
    ubuntu | debian | raspbian)
        UV_INSTALLED=false
        # 1) Try snap first (native on Ubuntu/Debian)
        if command -v snap >/dev/null 2>&1; then
            if [ ! -e /snap ] && [ -d /var/lib/snapd/snap ]; then
                sudo ln -s /var/lib/snapd/snap /snap
            fi
            sleep 2
            if sudo snap install astral-uv --classic 2>/dev/null; then
                log_message "uv installed via snap" "$GREEN"
                UV_INSTALLED=true
            else
                log_message "Snap installation failed (snap store unreachable or astral-uv unavailable)" "$YELLOW"
            fi
        fi
        # 2) Astral standalone installer — required on PEP 668 systems
        #    (Ubuntu 24.04+, Debian 12+, Python 3.12+) where 'pip install'
        #    refuses with externally-managed-environment. Installs a single
        #    static binary to /usr/local/bin so it is on root's PATH for the
        #    rest of this script and on every user's PATH for later use.
        if [ "$UV_INSTALLED" = false ]; then
            log_message "Installing uv via astral standalone installer..." "$BLUE"
            if curl -LsSf https://astral.sh/uv/install.sh | sudo env UV_INSTALL_DIR=/usr/local/bin INSTALLER_NO_MODIFY_PATH=1 sh; then
                log_message "uv installed to /usr/local/bin" "$GREEN"
                UV_INSTALLED=true
            fi
        fi
        # 3) Last resort: pip with --break-system-packages (PEP 668 override).
        if [ "$UV_INSTALLED" = false ]; then
            log_message "Astral installer failed, using pip with --break-system-packages..." "$YELLOW"
            sudo $PYTHON_CMD -m pip install --break-system-packages uv
            UV_INSTALLED=true
        fi
        check_status "Failed to install uv"
        ;;
    centos | fedora | rhel | amzn)
        UV_INSTALLED=false
        # Prefer astral standalone installer — works on PEP 668 systems
        # (Fedora 38+, RHEL/Rocky/Alma 9+ with newer Python) and avoids the
        # 'externally-managed-environment' error from system pip.
        log_message "Installing uv via astral standalone installer..." "$BLUE"
        if curl -LsSf https://astral.sh/uv/install.sh | sudo env UV_INSTALL_DIR=/usr/local/bin INSTALLER_NO_MODIFY_PATH=1 sh; then
            log_message "uv installed to /usr/local/bin" "$GREEN"
            UV_INSTALLED=true
        fi
        # Fallback to pip with --break-system-packages.
        if [ "$UV_INSTALLED" = false ]; then
            log_message "Astral installer failed, using pip fallback..." "$YELLOW"
            sudo $PYTHON_CMD -m pip install --break-system-packages uv
            UV_INSTALLED=true
        fi
        check_status "Failed to install uv"
        ;;
    arch)
        # Try pacman first, then pip with --break-system-packages for Arch
        log_message "Installing uv for Arch Linux..." "$BLUE"
        if sudo pacman -Sy --noconfirm --needed python-uv 2>/dev/null; then
            log_message "uv installed via pacman" "$GREEN"
        else
            log_message "uv not available in pacman, using pip..." "$YELLOW"
            sudo $PYTHON_CMD -m pip install --break-system-packages uv
            check_status "Failed to install uv"
        fi
        ;;
esac

# Install Certbot
log_message "\nInstalling Certbot..." "$BLUE"
case "$OS_TYPE" in
    ubuntu | debian | raspbian)
        # Wait for any running package manager operations to complete
        wait_for_dpkg_lock
        sudo apt-get install -y certbot python3-certbot-nginx
        check_status "Failed to install Certbot"
        ;;
    centos | fedora | rhel | amzn)
        # Try to install from package manager first
        CERTBOT_INSTALLED=false
        if ! command -v dnf >/dev/null 2>&1; then
            if sudo yum install -y certbot python3-certbot-nginx >/dev/null 2>&1; then
                CERTBOT_INSTALLED=true
                log_message "Certbot installed via yum" "$GREEN"
            fi
        else
            if sudo dnf install -y certbot python3-certbot-nginx >/dev/null 2>&1; then
                CERTBOT_INSTALLED=true
                log_message "Certbot installed via dnf" "$GREEN"
            fi
        fi

        # If package manager installation failed, try snap
        if [ "$CERTBOT_INSTALLED" = false ]; then
            log_message "Certbot not available in repositories, trying snap installation..." "$YELLOW"
            if command -v snap >/dev/null 2>&1; then
                if sudo snap install --classic certbot >/dev/null 2>&1; then
                    CERTBOT_INSTALLED=true
                    # Create symlink if installed via snap
                    sudo ln -sf /snap/bin/certbot /usr/bin/certbot 2>/dev/null || true
                    log_message "Certbot installed via snap" "$GREEN"
                fi
            fi
        fi

        # If still not installed, use pip as last resort
        if [ "$CERTBOT_INSTALLED" = false ]; then
            log_message "Installing Certbot via pip..." "$YELLOW"
            sudo $PYTHON_CMD -m pip install certbot certbot-nginx >/dev/null 2>&1
            if [ $? -eq 0 ]; then
                CERTBOT_INSTALLED=true
                log_message "Certbot installed via pip" "$GREEN"
            fi
        fi

        if [ "$CERTBOT_INSTALLED" = false ]; then
            log_message "Failed to install Certbot via all methods" "$RED"
            exit 1
        fi
        ;;
    arch)
        sudo pacman -Sy --noconfirm --needed certbot certbot-nginx
        check_status "Failed to install Certbot"
        ;;
esac

# Verify certbot is accessible
if ! command -v certbot >/dev/null 2>&1; then
    log_message "Error: Certbot installation failed - command not found" "$RED"
    exit 1
fi
log_message "Certbot installed successfully" "$GREEN"

# Check and handle existing OpenAlgo installation
handle_existing "$BASE_PATH" "installation directory" "OpenAlgo directory for $DEPLOY_NAME"

# Create base directory
log_message "\nCreating base directory..." "$BLUE"
sudo mkdir -p $BASE_PATH
check_status "Failed to create base directory"

# Clone repository
log_message "\nCloning OpenAlgo repository..." "$BLUE"
sudo git clone https://github.com/marketcalls/openalgo.git $OPENALGO_PATH
check_status "Failed to clone OpenAlgo repository"

# Create virtual environment using uv
log_message "\nSetting up Python virtual environment with uv..." "$BLUE"
if [ -d "$VENV_PATH" ]; then
    log_message "Warning: Virtual environment already exists, removing..." "$YELLOW"
    sudo rm -rf "$VENV_PATH"
fi
# Create directory if it doesn't exist
sudo mkdir -p $(dirname $VENV_PATH)

# Detect how uv is installed and set the appropriate command
if command -v uv >/dev/null 2>&1; then
    # uv is available as a standalone command (snap or astral installer)
    UV_CMD="uv"
    log_message "Using standalone uv command" "$GREEN"
elif $PYTHON_CMD -m uv --version >/dev/null 2>&1; then
    # uv is available as a Python module
    UV_CMD="$PYTHON_CMD -m uv"
    log_message "Using uv as Python module" "$GREEN"
else
    log_message "Error: uv is not available" "$RED"
    exit 1
fi

# Create virtual environment using uv
sudo $UV_CMD venv $VENV_PATH
check_status "Failed to create virtual environment with uv"

# Install Python dependencies using uv (faster installation)
log_message "\nInstalling Python dependencies with uv..." "$BLUE"
# First activate the virtual environment path for uv
ACTIVATE_CMD="source $VENV_PATH/bin/activate"
# Install dependencies using uv
sudo $UV_CMD pip install --python $VENV_PATH/bin/python -r $OPENALGO_PATH/requirements-nginx.txt
check_status "Failed to install Python dependencies"

# Verify gunicorn and eventlet installation
log_message "\nVerifying gunicorn and eventlet installation..." "$BLUE"
if ! sudo bash -c "$ACTIVATE_CMD && pip freeze | grep -q 'gunicorn=='"; then
    log_message "Installing gunicorn..." "$YELLOW"
    sudo $UV_CMD pip install --python $VENV_PATH/bin/python "gunicorn>=25.0,<26"
    check_status "Failed to install gunicorn"
fi
if ! sudo bash -c "$ACTIVATE_CMD && pip freeze | grep -q 'eventlet=='"; then
    log_message "Installing eventlet..." "$YELLOW"
    sudo $UV_CMD pip install --python $VENV_PATH/bin/python eventlet
    check_status "Failed to install eventlet"
fi

# Configure .env file
log_message "\nConfiguring environment file..." "$BLUE"
handle_existing "$OPENALGO_PATH/.env" "environment file" ".env file"

sudo cp $OPENALGO_PATH/.sample.env $OPENALGO_PATH/.env
sudo sed -i "s|YOUR_BROKER_API_KEY|$BROKER_API_KEY|g" $OPENALGO_PATH/.env
sudo sed -i "s|YOUR_BROKER_API_SECRET|$BROKER_API_SECRET|g" $OPENALGO_PATH/.env

# Update market data API credentials if the broker is XTS-based
if is_xts_broker "$BROKER_NAME"; then
    sudo sed -i "s|YOUR_BROKER_MARKET_API_KEY|$BROKER_API_KEY_MARKET|g" $OPENALGO_PATH/.env
    sudo sed -i "s|YOUR_BROKER_MARKET_API_SECRET|$BROKER_API_SECRET_MARKET|g" $OPENALGO_PATH/.env
fi

sudo sed -i "s|http://127.0.0.1:5000|https://$DOMAIN|g" $OPENALGO_PATH/.env
# Explicitly set HOST_SERVER in case the default value didn't match
sudo sed -i "s|HOST_SERVER = '.*'|HOST_SERVER = 'https://$DOMAIN'|g" $OPENALGO_PATH/.env
sudo sed -i "s|<broker>|$BROKER_NAME|g" $OPENALGO_PATH/.env
sudo sed -i "s|OPENALGO_PLACEHOLDER_APP_KEY_REGENERATE_BEFORE_USE|$APP_KEY|g" $OPENALGO_PATH/.env
sudo sed -i "s|OPENALGO_PLACEHOLDER_API_KEY_PEPPER_REGENERATE_BEFORE_USE|$API_KEY_PEPPER|g" $OPENALGO_PATH/.env

# This deployment runs gunicorn behind the nginx reverse proxy configured below
# (Unix socket bind, not directly reachable from the internet). The proxy sets
# X-Forwarded-For / X-Real-IP for IP-based features; trust those headers.
sudo sed -i "s|TRUST_PROXY_HEADERS = 'FALSE'|TRUST_PROXY_HEADERS = 'TRUE'|g" $OPENALGO_PATH/.env

# Disable session expiry for crypto brokers (24/7 markets)
if [ "$DISABLE_SESSION_EXPIRY" = "true" ]; then
    sudo sed -i "s|DISABLE_SESSION_EXPIRY = 'false'|DISABLE_SESSION_EXPIRY = 'true'|g" $OPENALGO_PATH/.env
    log_message "Session auto-logout disabled for crypto broker" "$GREEN"
fi

# Update WebSocket URL for production
sudo sed -i "s|WEBSOCKET_URL='.*'|WEBSOCKET_URL='wss://$DOMAIN/ws'|g" $OPENALGO_PATH/.env

# Enable Remote MCP if the operator opted in. Same-domain mode: /mcp and
# /oauth/* are served from the same nginx vhost as the dashboard, no
# extra config needed. Other MCP_* keys (auto-approve, write scope, CORS
# allowlist) inherit their defaults from .sample.env — flip them later
# in .env if you want stricter behavior on a shared deployment.
if [ "$ENABLE_REMOTE_MCP" = "true" ]; then
    sudo sed -i "s|MCP_HTTP_ENABLED = 'False'|MCP_HTTP_ENABLED = 'True'|g" $OPENALGO_PATH/.env
    sudo sed -i "s|MCP_PUBLIC_URL = ''|MCP_PUBLIC_URL = 'https://$DOMAIN'|g" $OPENALGO_PATH/.env
    log_message "Remote MCP enabled at https://$DOMAIN/mcp" "$GREEN"
fi

# Host bindings intentionally left at 127.0.0.1 (the .sample.env default):
# - nginx on this host reverse-proxies /ws -> 127.0.0.1:WEBSOCKET_PORT, so the
#   WebSocket server does not need to listen on all interfaces.
# - ZMQ is an internal message bus between broker adapters and the WS proxy;
#   binding it to 0.0.0.0 would expose the raw tick feed to the public IP.

check_status "Failed to configure environment file"

# Check and handle existing Nginx configuration
handle_existing "$NGINX_CONFIG_FILE" "Nginx configuration" "Nginx config file"

# Fix Arch Linux nginx.conf to include conf.d directory
if [ "$OS_TYPE" = "arch" ]; then
    if ! grep -q "include.*conf.d/\*.conf" /etc/nginx/nginx.conf; then
        log_message "Adding conf.d include to nginx.conf for Arch Linux..." "$YELLOW"
        sudo sed -i '/http {/a\    include /etc/nginx/conf.d/*.conf;' /etc/nginx/nginx.conf
        log_message "conf.d include added to nginx.conf" "$GREEN"
    fi
fi

# Configure initial Nginx for SSL certificate obtention
log_message "\nConfiguring initial Nginx setup..." "$BLUE"
sudo tee $NGINX_CONFIG_FILE > /dev/null << EOL
server {
    listen 80;
    listen [::]:80;
    server_name $DOMAIN;
    root /var/www/html;
    
    location / {
        try_files \$uri \$uri/ =404;
    }
}
EOL

# Enable site and remove default configuration
if [ "$NGINX_CONFIG_MODE" = "sites" ]; then
    sudo rm -f /etc/nginx/sites-enabled/default
    sudo ln -sf $NGINX_CONFIG_FILE /etc/nginx/sites-enabled/
    check_status "Failed to enable Nginx site"
else
    # For conf.d mode, config is already active, just remove default if it exists
    sudo rm -f /etc/nginx/conf.d/default.conf
fi

# Start or reload Nginx for initial configuration
log_message "\nTesting and starting/reloading Nginx..." "$BLUE"
sudo nginx -t
check_status "Failed to validate Nginx configuration"

# Check if nginx is running, start or reload accordingly
if sudo systemctl is-active --quiet nginx; then
    sudo systemctl reload nginx
    log_message "Nginx reloaded successfully" "$GREEN"
else
    sudo systemctl enable nginx
    sudo systemctl start nginx
    log_message "Nginx started successfully" "$GREEN"
fi
check_status "Failed to start/reload Nginx"

# Configure firewall
log_message "\nConfiguring firewall rules..." "$BLUE"
case "$OS_TYPE" in
    ubuntu | debian | raspbian)
        # Wait for any running package manager operations to complete
        wait_for_dpkg_lock
        sudo apt-get install -y ufw
        sudo ufw default deny incoming
        sudo ufw default allow outgoing
        sudo ufw allow ssh
        sudo ufw allow 'Nginx Full'
        sudo ufw --force enable
        check_status "Failed to configure firewall"
        ;;
    centos | fedora | rhel | amzn)
        # Install and configure firewalld
        if ! command -v firewall-cmd >/dev/null 2>&1; then
            if ! command -v dnf >/dev/null 2>&1; then
                sudo yum install -y firewalld
            else
                sudo dnf install -y firewalld
            fi
        fi
        sudo systemctl enable firewalld
        sudo systemctl start firewalld
        sudo firewall-cmd --permanent --add-service=ssh
        sudo firewall-cmd --permanent --add-service=http
        sudo firewall-cmd --permanent --add-service=https
        sudo firewall-cmd --reload
        check_status "Failed to configure firewall"
        ;;
    arch)
        # Install ufw on Arch
        if ! command -v ufw >/dev/null 2>&1; then
            sudo pacman -Sy --noconfirm --needed ufw
        fi
        sudo systemctl enable ufw
        sudo systemctl start ufw
        sudo ufw default deny incoming
        sudo ufw default allow outgoing
        sudo ufw allow ssh
        # Use direct port rules instead of application profile on Arch
        sudo ufw allow 80/tcp
        sudo ufw allow 443/tcp
        sudo ufw --force enable
        check_status "Failed to configure firewall"
        ;;
esac

# Obtain SSL certificate
log_message "\nObtaining SSL certificate..." "$BLUE"
if [ "$IS_SUBDOMAIN" = true ]; then
    sudo certbot --nginx -d $DOMAIN --non-interactive --agree-tos --email admin@${DOMAIN#*.}
else
    sudo certbot --nginx -d $DOMAIN -d www.$DOMAIN --non-interactive --agree-tos --email admin@$DOMAIN
fi

# Check if certificate was obtained (even if auto-install failed)
if [ ! -f "/etc/letsencrypt/live/$DOMAIN/fullchain.pem" ]; then
    log_message "Failed to obtain SSL certificate" "$RED"
    exit 1
else
    log_message "SSL certificate obtained successfully" "$GREEN"
fi

# Configure final Nginx setup with SSL and socket
log_message "\nConfiguring final Nginx setup..." "$BLUE"
# Remove the existing openalgo nginx config and any legacy domain-keyed
# files left over from older installs (pre-simple-paths) so the rewrite
# below leaves exactly one openalgo vhost on disk.
sudo rm -f $NGINX_CONFIG_FILE
sudo rm -f ${NGINX_AVAILABLE}/${DOMAIN} ${NGINX_AVAILABLE}/${DOMAIN}.conf
if [ "$NGINX_CONFIG_MODE" = "sites" ]; then
    sudo rm -f /etc/nginx/sites-enabled/openalgo.conf
    sudo rm -f /etc/nginx/sites-enabled/${DOMAIN}
    sudo rm -f /etc/nginx/sites-enabled/${DOMAIN}.conf
fi
# Write the new configuration
sudo tee $NGINX_CONFIG_FILE > /dev/null << EOL
server {
    listen 80;
    listen [::]:80;
    server_name $DOMAIN;

    # WebSocket path exceptions to avoid 301 redirect loop
    location = /ws {
        return 301 https://\$host\$request_uri;
    }

    location /ws/ {
        return 301 https://\$host\$request_uri;
    }

    # All other HTTP requests get redirected to HTTPS
    location / {
        return 301 https://\$host\$request_uri;
    }
}

server {
    listen 443 ssl;
    listen [::]:443 ssl;
    
    server_name $DOMAIN;
    
    ssl_certificate /etc/letsencrypt/live/$DOMAIN/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/$DOMAIN/privkey.pem;
    
    # SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers on;
    ssl_ciphers EECDH+AESGCM:EDH+AESGCM;
    ssl_ecdh_curve secp384r1;
    ssl_session_timeout 10m;
    ssl_session_cache shared:SSL:10m;
    ssl_session_tickets off;
    ssl_stapling on;
    ssl_stapling_verify on;
    
    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=63072000" always;

    # WebSocket without trailing slash
    location = /ws {
        proxy_pass http://127.0.0.1:8765;
        proxy_http_version 1.1;
        
        # Extended timeouts for long-running connections (up to 24 hours)
        proxy_read_timeout 86400s;
        proxy_send_timeout 86400s;
        
        # Disable proxy buffering for real-time data
        proxy_buffering off;
        
        # WebSocket headers
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # Other headers
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_set_header X-Forwarded-Host \$host;
    }

    # WebSocket with trailing slash
    location /ws/ {
        proxy_pass http://127.0.0.1:8765/;
        proxy_http_version 1.1;

        # Extended timeouts for long-running connections (up to 24 hours)
        proxy_read_timeout 86400s;
        proxy_send_timeout 86400s;

        # Disable proxy buffering for real-time data
        proxy_buffering off;

        # WebSocket headers
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";

        # Other headers
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_set_header X-Forwarded-Host \$host;
    }

    # Socket.IO (Flask-SocketIO real-time events)
    location /socket.io/ {
        proxy_pass http://unix:$SOCKET_FILE;
        proxy_http_version 1.1;

        # Extended timeouts for long-lived Socket.IO sessions
        proxy_read_timeout 86400s;
        proxy_send_timeout 86400s;

        # Disable proxy buffering for real-time events
        proxy_buffering off;

        # WebSocket upgrade headers (required for Socket.IO WebSocket transport)
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";

        # Other headers
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_set_header X-Forwarded-Host \$host;
    }

    # Main app (Gunicorn UDS)
    location / {
        proxy_pass http://unix:$SOCKET_FILE;
        proxy_http_version 1.1;

        # Extended timeouts for broker authentication (cold start can take 60-90s)
        proxy_read_timeout 300s;
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;

        # Increased buffer sizes for large headers (auth tokens, session cookies)
        proxy_buffer_size 128k;
        proxy_buffers 4 256k;
        proxy_busy_buffers_size 256k;

        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_redirect off;
    }
}
EOL

# Recreate symlink for sites-enabled if needed
if [ "$NGINX_CONFIG_MODE" = "sites" ]; then
    sudo ln -sf $NGINX_CONFIG_FILE /etc/nginx/sites-enabled/
    log_message "Recreated nginx symlink" "$GREEN"
fi

# Test Nginx configuration
log_message "\nTesting Nginx configuration..." "$BLUE"
sudo nginx -t
check_status "Failed to validate Nginx configuration"

# Check and handle existing systemd service
handle_existing "/etc/systemd/system/$SERVICE_NAME.service" "systemd service" "OpenAlgo service file"

# Create systemd service with unique name
log_message "\nCreating systemd service..." "$BLUE"
sudo tee /etc/systemd/system/$SERVICE_NAME.service > /dev/null << EOL
[Unit]
Description=OpenAlgo Gunicorn Daemon ($DEPLOY_NAME)
After=network.target

[Service]
User=$WEB_USER
Group=$WEB_GROUP
WorkingDirectory=$OPENALGO_PATH
# Set HOME so Kaleido/choreographer can write temp files for Telegram /chart.
# Kaleido 1.x creates temp dirs in Path.home() (not TMPDIR); the default
# www-data home /var/www/ is typically root-owned and not writable.
Environment="HOME=$OPENALGO_PATH/tmp"
# Environment variables for numba/scipy support
Environment="TMPDIR=$OPENALGO_PATH/tmp"
Environment="NUMBA_CACHE_DIR=$OPENALGO_PATH/tmp/numba_cache"
Environment="LLVMLITE_TMPDIR=$OPENALGO_PATH/tmp"
Environment="MPLCONFIGDIR=$OPENALGO_PATH/tmp/matplotlib"
# Thread limits for OpenBLAS/NumPy to prevent RLIMIT_NPROC issues
# See: https://github.com/marketcalls/openalgo/issues/822
Environment="OPENBLAS_NUM_THREADS=2"
Environment="OMP_NUM_THREADS=2"
Environment="MKL_NUM_THREADS=2"
Environment="NUMEXPR_NUM_THREADS=2"
Environment="NUMBA_NUM_THREADS=2"
# Simplified approach to ensure Python environment is properly loaded
ExecStart=/bin/bash -c 'source $VENV_PATH/bin/activate && $VENV_PATH/bin/gunicorn \
    --worker-class eventlet \
    -w 1 \
    --bind unix:$SOCKET_FILE \
    --timeout 300 \
    --log-level info \
    app:app'
# Restart settings
Restart=always
RestartSec=5
TimeoutSec=300

[Install]
WantedBy=multi-user.target
EOL
check_status "Failed to create systemd service"

# Set correct permissions
log_message "\nSetting permissions..." "$BLUE"

# Set permissions for base directory
sudo chown -R $WEB_USER:$WEB_GROUP $BASE_PATH
sudo chmod -R 755 $BASE_PATH

# Create and set permissions for required directories
sudo mkdir -p $OPENALGO_PATH/db
sudo mkdir -p $OPENALGO_PATH/tmp/numba_cache
sudo mkdir -p $OPENALGO_PATH/tmp/matplotlib
# Create directories for Python strategy feature
sudo mkdir -p $OPENALGO_PATH/strategies/scripts
sudo mkdir -p $OPENALGO_PATH/strategies/examples
sudo mkdir -p $OPENALGO_PATH/log/strategies
sudo mkdir -p $OPENALGO_PATH/keys
# Set ownership and permissions
sudo chown -R $WEB_USER:$WEB_GROUP $OPENALGO_PATH
sudo chmod -R 755 $OPENALGO_PATH
# Set more restrictive permissions for sensitive directories
sudo chmod 700 $OPENALGO_PATH/keys
# Restrict .env to the service account only — contains APP_KEY, API_KEY_PEPPER,
# broker API credentials, and SMTP password. The recursive chmod 755 above
# would otherwise leave it world-readable on shared boxes.
sudo chmod 600 $OPENALGO_PATH/.env

# Remove existing socket file if it exists
[ -S "$SOCKET_FILE" ] && sudo rm -f $SOCKET_FILE

# Ensure socket directory is accessible to nginx
sudo chmod 755 $SOCKET_PATH

# Verify permissions
log_message "\nVerifying permissions..." "$BLUE"
ls -la $OPENALGO_PATH
check_status "Failed to set permissions"

# Reload systemd and start services
log_message "\nStarting services..." "$BLUE"
sudo systemctl daemon-reload
sudo systemctl enable $SERVICE_NAME
sudo systemctl start $SERVICE_NAME
sudo systemctl restart nginx
check_status "Failed to start services"

# Configure SELinux for RHEL-based systems
if [ "$OS_TYPE" = "centos" ] || [ "$OS_TYPE" = "fedora" ] || [ "$OS_TYPE" = "rhel" ] || [ "$OS_TYPE" = "amzn" ]; then
    if command -v getenforce >/dev/null 2>&1 && [ "$(getenforce)" != "Disabled" ]; then
        log_message "\nConfiguring SELinux permissions..." "$BLUE"

        # Set SELinux context for the application directory
        sudo semanage fcontext -a -t httpd_sys_rw_content_t "$BASE_PATH(/.*)?" 2>/dev/null || true
        sudo restorecon -Rv $BASE_PATH >/dev/null 2>&1

        # Enable httpd network connections
        sudo setsebool -P httpd_can_network_connect on 2>/dev/null || true

        # Check for SELinux denials and create policy if needed
        if sudo ausearch -m avc -ts recent 2>/dev/null | grep -q "httpd_t.*initrc_t.*unix_stream_socket"; then
            log_message "Creating SELinux policy for nginx-gunicorn connection..." "$YELLOW"

            # Generate and install SELinux policy for httpd to connect to gunicorn socket
            sudo ausearch -m avc -ts recent 2>/dev/null | sudo audit2allow -M httpd_gunicorn 2>/dev/null || true
            if [ -f httpd_gunicorn.pp ]; then
                sudo semodule -i httpd_gunicorn.pp 2>/dev/null || true
                sudo rm -f httpd_gunicorn.pp httpd_gunicorn.te 2>/dev/null || true
                log_message "SELinux policy installed successfully" "$GREEN"

                # Restart nginx to apply new policy
                sudo systemctl restart nginx
            fi
        fi

        log_message "SELinux configuration completed" "$GREEN"
    fi
fi

log_message "\nInstallation completed successfully!" "$GREEN"
log_message "\nInstallation Summary:" "$YELLOW"
log_message "Operating System: $OS_TYPE $OS_VERSION" "$BLUE"
log_message "Deployment Name: $DEPLOY_NAME" "$BLUE"
log_message "Domain: $DOMAIN" "$BLUE"
log_message "Broker: $BROKER_NAME" "$BLUE"
log_message "Installation Directory: $OPENALGO_PATH" "$BLUE"
log_message "Environment File: $OPENALGO_PATH/.env" "$BLUE"
log_message "Socket File: $SOCKET_FILE" "$BLUE"
log_message "Service Name: $SERVICE_NAME" "$BLUE"
log_message "Nginx Config: $NGINX_CONFIG_FILE" "$BLUE"
log_message "SSL: Enabled with Let's Encrypt" "$BLUE"
if [ "$DISABLE_SESSION_EXPIRY" = "true" ]; then
    log_message "Auto-Logout: Disabled (24/7 crypto market)" "$BLUE"
else
    log_message "Auto-Logout: Enabled (3 AM IST daily)" "$BLUE"
fi
if [ "$ENABLE_REMOTE_MCP" = "true" ]; then
    log_message "Remote MCP: Enabled at https://$DOMAIN/mcp" "$BLUE"
else
    log_message "Remote MCP: Disabled" "$BLUE"
fi
log_message "Installation Log: $LOG_FILE" "$BLUE"

log_message "\nNext Steps:" "$YELLOW"
log_message "1. Visit https://$DOMAIN to access your OpenAlgo instance" "$GREEN"
log_message "2. Configure your broker settings in the web interface" "$GREEN"
log_message "3. Review the logs using: sudo journalctl -u $SERVICE_NAME" "$GREEN"
log_message "4. Monitor the application status: sudo systemctl status $SERVICE_NAME" "$GREEN"

log_message "\nUseful Commands:" "$YELLOW"
log_message "Restart OpenAlgo: sudo systemctl restart $SERVICE_NAME" "$BLUE"
log_message "View Logs: sudo journalctl -u $SERVICE_NAME" "$BLUE"
log_message "Check Status: sudo systemctl status $SERVICE_NAME" "$BLUE"
log_message "View Installation Log: cat $LOG_FILE" "$BLUE"

```


---

# FILE: install\README.md

```md
# OpenAlgo Installation Guide

## Prerequisites

### System Requirements
- **Supported Linux Distributions:**
  - **Debian-based:** Ubuntu (22.04+ LTS), Debian, Raspbian, Pop!_OS, Linux Mint, Zorin OS
  - **RHEL-based:** CentOS, RHEL, Fedora, Rocky Linux, AlmaLinux, Amazon Linux, Oracle Linux
  - **Arch-based:** Arch Linux, Manjaro, EndeavourOS, CachyOS
- Minimum 2GB RAM (script will configure swap if needed)
- Clean installation recommended

### Domain and DNS Setup (Required)
1. **Cloudflare Account Setup**
   - Create a Cloudflare account if you don't have one
   - Add your domain to Cloudflare
   - Update your domain's nameservers to Cloudflare's nameservers

2. **DNS Configuration**
   - Add an A record pointing to your server's IP address
     ```
     Type: A
     Name: yourdomain.com
     Content: YOUR_SERVER_IP
     Proxy status: Proxied
     ```
   - Add a CNAME record for www subdomain
     ```
     Type: CNAME
     Name: www
     Content: yourdomain.com
     Proxy status: Proxied
     ```

3. **SSL/TLS Configuration in Cloudflare**
   - Go to SSL/TLS section
   - Set encryption mode to "Full (strict)"

### Broker Setup (Required)
- Choose your broker from the supported list:
  ```
  fivepaisa, fivepaisaxts, aliceblue, angel, compositedge, definedge, deltaexchange, dhan, dhan_sandbox,
  firstock, flattrade, fyers, groww, ibulls, iifl, iiflcaital, indmoney, jainamxts, kotak, motilal,
  mstock, nubra, paytm, pocketful, rmoney, samco, shoonya, tradejini, upstox, wisdom, zebu, zerodha
  ```
- Obtain your broker's API credentials:
  - API Key
  - API Secret
- XTS brokers also need market data credentials:
  - `fivepaisaxts`, `compositedge`, `ibulls`, `iifl`, `jainamxts`, `rmoney`, `wisdom`

## Installation Steps

### 1. Download Installation Script
```bash
# Connect to your Linux server via SSH
ssh user@your_server_ip

# Create a directory for installation
mkdir -p ~/openalgo-install
cd ~/openalgo-install

# Download the installation script
wget https://raw.githubusercontent.com/marketcalls/openalgo/main/install/install.sh

# Or using curl
curl -O https://raw.githubusercontent.com/marketcalls/openalgo/main/install/install.sh

# Make the script executable
chmod +x install.sh
```

### 2. Run Installation Script
```bash
# Execute the installation script
sudo ./install.sh
```

The script will interactively prompt you for:
- Your domain name (supports both root domains and subdomains)
- Broker selection
- Broker API credentials

The installation process will:
- **Detect your Linux distribution** and use appropriate package managers
- Install required packages (Python, Nginx, Git, Certbot, UV)
- Configure system swap memory if needed (for systems with <2GB RAM)
- Set timezone to IST (optional)
- Configure firewall (UFW for Debian/Arch, firewalld for RHEL)
- **Auto-configure SELinux** on RHEL-based systems
- Obtain and install Let's Encrypt SSL certificate
- Configure Nginx with SSL and WebSocket support
- Set up the OpenAlgo application with unique deployment name
- Create systemd service with unique name based on domain and broker
- Generate detailed installation logs in the logs directory

#### Multi-Domain Deployment
The installation script supports deploying multiple instances on the same server:
- Each deployment gets a unique service name (e.g., openalgo-yourdomain-broker)
- Separate configuration files and directories for each deployment
- Individual log files for each installation in the logs directory
- Independent SSL certificates for each domain
- Isolated Python virtual environments

Example of running multiple deployments:
```bash
# First deployment
sudo ./install.sh
# Enter domain: trading1.yourdomain.com
# Enter broker: fyers

# Second deployment
sudo ./install.sh
# Enter domain: trading2.yourdomain.com
# Enter broker: zerodha
```

Each deployment will:
- Have its own systemd service
- Use separate configuration files
- Store logs in unique timestamped files
- Run independently of other deployments

### 3. Verify Installation

After installation completes, verify each deployment:

1. **Check Service Status**
   ```bash
   # Example for Fyers deployment
   sudo systemctl status openalgo-fyers-yourdomain-fyers
   
   # Example for Zerodha deployment
   sudo systemctl status openalgo-zerodha-yourdomain-zerodha
   ```

2. **Verify Nginx Configuration**
   ```bash
   # Test overall Nginx configuration
   sudo nginx -t

   # Check specific site configurations
   # For Debian/Ubuntu (sites-enabled):
   ls -l /etc/nginx/sites-enabled/
   cat /etc/nginx/sites-enabled/fyers.yourdomain.com

   # For RHEL/CentOS/Arch (conf.d):
   ls -l /etc/nginx/conf.d/
   cat /etc/nginx/conf.d/fyers.yourdomain.com.conf
   ```

3. **Access Web Interfaces**
   Test each deployment in your web browser:
   ```
   https://fyers.yourdomain.com
   https://zerodha.yourdomain.com
   ```

4. **Check Installation Logs**
   ```bash
   # View the installation log for your deployment
   cat install/logs/install_YYYYMMDD_HHMMSS.log
   ```

## Troubleshooting

### Common Issues

1. **SSL Certificate Issues**
   ```bash
   # Check Certbot logs
   sudo journalctl -u certbot
   
   # Example: Manually run certificate installation for trading.yourdomain.com
   sudo certbot --nginx -d trading.yourdomain.com
   
   # Example: Manually run certificate installation for multiple subdomains
   sudo certbot --nginx -d fyers.yourdomain.com -d zerodha.yourdomain.com
   ```

2. **Application Not Starting**
   Example scenario: Managing multiple broker deployments
   ```bash
   # Example 1: Fyers deployment on fyers.yourdomain.com
   sudo journalctl -u openalgo-fyers-yourdomain-fyers    # View logs
   sudo systemctl restart openalgo-fyers-yourdomain-fyers # Restart service
   
   # Example 2: Zerodha deployment on zerodha.yourdomain.com
   sudo journalctl -u openalgo-zerodha-yourdomain-zerodha # View logs
   sudo systemctl restart openalgo-zerodha-yourdomain-zerodha # Restart service
   ```

3. **Nginx Issues**
   ```bash
   # Check Nginx error logs for all deployments
   sudo tail -f /var/log/nginx/error.log
   
   # Check access logs for specific domains
   sudo tail -f /var/log/nginx/fyers.yourdomain.com.access.log
   sudo tail -f /var/log/nginx/zerodha.yourdomain.com.access.log
   ```

4. **Installation Logs**
   Example: Checking installation logs for multiple deployments
   ```bash
   # List all installation logs
   ls -l install/logs/
   
   # View latest installation log
   cat install/logs/$(ls -t install/logs/ | head -1)
   
   # Example: View specific deployment logs
   cat install/logs/install_20240101_120000.log  # Fyers installation
   cat install/logs/install_20240101_143000.log  # Zerodha installation
   ```

### Distribution-Specific Troubleshooting

#### Arch Linux

1. **Nginx not listening on port 443**
   ```bash
   # Check if conf.d is included in nginx.conf
   grep "conf.d" /etc/nginx/nginx.conf

   # If missing, add it manually
   sudo sed -i '/http {/a\    include /etc/nginx/conf.d/*.conf;' /etc/nginx/nginx.conf
   sudo systemctl restart nginx
   ```

2. **UV installation issues**
   ```bash
   # Install via pacman
   sudo pacman -Sy python-uv

   # Or use pip with system packages override
   sudo python -m pip install --break-system-packages uv
   ```

#### RHEL/CentOS/Fedora

1. **SELinux blocking Nginx**
   ```bash
   # Check SELinux status
   getenforce

   # View SELinux denials
   sudo ausearch -m avc -ts recent

   # The script auto-configures SELinux, but if issues persist:
   sudo setsebool -P httpd_can_network_connect on
   sudo semanage fcontext -a -t httpd_sys_rw_content_t "/var/python/openalgo-flask(/.*)?"
   sudo restorecon -Rv /var/python/openalgo-flask
   ```

2. **Firewalld not configured**
   ```bash
   # Check firewall status
   sudo firewall-cmd --list-all

   # Manually add rules if needed
   sudo firewall-cmd --permanent --add-service=http
   sudo firewall-cmd --permanent --add-service=https
   sudo firewall-cmd --reload
   ```

#### Cloudflare 521 Error

1. **Set SSL/TLS mode to "Full (strict)"**
   - Go to Cloudflare Dashboard → SSL/TLS → Overview
   - Change encryption mode from "Flexible" to "Full (strict)"

2. **Temporarily disable proxy for testing**
   - Go to DNS tab
   - Click orange cloud icon → turns grey (DNS only)
   - Test your site directly
   - Re-enable proxy after confirming server works

### Managing Multiple Deployments

1. **Service Management Examples**
   ```bash
   # List all OpenAlgo services
   systemctl list-units "openalgo-*"
   
   # Example outputs:
   # openalgo-fyers-yourdomain-fyers.service    loaded active running
   # openalgo-zerodha-yourdomain-zerodha.service loaded active running
   
   # Restart specific deployment
   sudo systemctl restart openalgo-fyers-yourdomain-fyers
   
   # Check status of specific deployment
   sudo systemctl status openalgo-zerodha-yourdomain-zerodha
   ```

2. **Log Management Examples**
   ```bash
   # View real-time logs for Fyers deployment
   sudo journalctl -f -u openalgo-fyers-yourdomain-fyers
   
   # View last 100 lines of Zerodha deployment logs
   sudo journalctl -n 100 -u openalgo-zerodha-yourdomain-zerodha
   
   # View logs since last hour for specific deployment
   sudo journalctl --since "1 hour ago" -u openalgo-fyers-yourdomain-fyers
   ```

3. **Nginx Configuration Examples**
   ```bash
   # View Nginx configs for different deployments
   sudo nano /etc/nginx/sites-available/fyers.yourdomain.com
   sudo nano /etc/nginx/sites-available/zerodha.yourdomain.com
   
   # Test Nginx configuration
   sudo nginx -t
   
   # Reload Nginx after config changes
   sudo systemctl reload nginx
   ```

4. **Installation Directory Examples**
   ```bash
   # List deployment directories
   ls -l /var/python/openalgo-flask/
   
   # Example structure:
   # /var/python/openalgo-flask/fyers-yourdomain-fyers/
   # /var/python/openalgo-flask/zerodha-yourdomain-zerodha/
   
   # Check specific deployment files
   ls -l /var/python/openalgo-flask/fyers-yourdomain-fyers/
   ```

## Security Notes

1. **Firewall**
   - **Debian/Ubuntu/Arch:** Configures UFW to allow only HTTP, HTTPS, and SSH
   - **RHEL/CentOS/Fedora:** Configures firewalld to allow only HTTP, HTTPS, and SSH
   - Additional ports can be opened if needed:
     ```bash
     # For UFW (Debian/Ubuntu/Arch)
     sudo ufw allow <port_number>

     # For firewalld (RHEL/CentOS/Fedora)
     sudo firewall-cmd --permanent --add-port=<port_number>/tcp
     sudo firewall-cmd --reload
     ```

2. **SELinux (RHEL-based systems)**
   - The installation script **automatically configures SELinux** for OpenAlgo
   - Sets correct contexts for application directories
   - Enables httpd network connections
   - Creates custom policies if needed
   - No manual SELinux configuration required!

3. **SSL/TLS**
   - Certificates are automatically renewed by Certbot
   - The installation configures modern SSL parameters
   - Regular updates are recommended:
     ```bash
     # For Debian/Ubuntu
     sudo apt update && sudo apt upgrade -y

     # For RHEL/CentOS/Fedora
     sudo dnf update -y
     # or on older systems
     sudo yum update -y

     # For Arch Linux
     sudo pacman -Syu
     ```

## Post-Installation

1. Configure your broker settings in the web interface
2. Set up monitoring and alerts if needed
3. Regularly check logs for any issues
4. Keep the system updated with security patches

## Support

For issues and support:
- Check the [GitHub repository](https://github.com/marketcalls/openalgo)
- Review the logs using commands provided above
- Contact support with relevant log information

Remember to:
- Regularly backup your configuration
- Monitor system resources
- Keep the system updated
- Review security best practices

```


---

# FILE: install\Remote-MCP-readme.md

```md
# Remote MCP — Install Guide

> **Status:** opt-in feature shipped on the `remotemcp` branch
> **Default:** off — installs that don't run the enable helper see no
> behavior change, the local stdio MCP keeps working unchanged.

## What this gets you

Once enabled, hosted AI clients (claude.ai, chatgpt.com, claude mobile)
can connect to your OpenAlgo install over HTTPS using OAuth 2.1 with
PKCE. Tools the user authorizes become callable from those clients.

The local stdio MCP (`mcp/mcpserver.py` launched by Claude Desktop /
Cursor / Windsurf) is **completely unaffected** by this feature. Both
transports share the same tool definitions but live in separate code
paths.

See `docs/prd/remote-mcp.md` for the full architecture and threat
model.

---

## Pick your install path

| Your install came from | Use this enabler |
|---|---|
| `install/install.sh` (native Ubuntu, single domain) | `sudo ./install/enable-remote-mcp.sh` |
| `install/install-multi.sh` (native Ubuntu, multiple domains) | `sudo ./install/enable-remote-mcp.sh` — the helper detects all `openalgo-*` services and asks which one |
| `install/install-docker.sh` (single Docker stack) | `sudo ./install/enable-remote-mcp-docker.sh` |
| `install/install-docker-multi-custom-ssl.sh` (multi-instance Docker) | `sudo ./install/enable-remote-mcp-docker.sh` — re-run for each domain you want to enable |

Both helpers default to **same-domain mode** (MCP lives at
`https://<your-existing-domain>/mcp` — no DNS work, no extra cert).
Subdomain mode is documented at the bottom of this file as a manual
recipe.

## Mode 1 — Same-domain (recommended for most users)

This is the path the helper scripts automate. The MCP and OAuth
endpoints live under your existing OpenAlgo dashboard hostname, e.g.
`https://yourdomain.com/mcp`.

**No nginx changes are needed.** The existing `location /` block in
the install scripts' nginx config already proxies every path to
Gunicorn — `/mcp`, `/oauth/*`, and `/.well-known/oauth-*` ride that
same proxy.

### Steps for native Ubuntu installs (`install.sh`, `install-multi.sh`)

```bash
# After install/install.sh (or install-multi.sh) has completed and
# your dashboard is reachable, run this from the openalgo project
# root:
sudo ./install/enable-remote-mcp.sh
```

The script:

1. Detects the existing `openalgo-*` systemd service
2. Reads your `.env` to suggest the right public URL
3. Refuses if `FLASK_DEBUG=True` (token leak risk)
4. Backs up your `.env`, then sets:
   - `MCP_HTTP_ENABLED=True`
   - `MCP_PUBLIC_URL=https://yourdomain.com`
   - `MCP_OAUTH_REQUIRE_APPROVAL=True`
   - `MCP_OAUTH_WRITE_SCOPE_ENABLED=False`
5. Ensures `keys/` exists with `chmod 700`
6. Restarts the service (which auto-generates the RS256 signing key)
7. Probes the discovery / JWKS / healthz endpoints to confirm they
   respond

**Total downtime:** one Gunicorn restart (~3 seconds).

### Steps for Docker installs (`install-docker.sh`, `install-docker-multi-custom-ssl.sh`)

```bash
# After your container(s) are running, from the openalgo project root:
sudo ./install/enable-remote-mcp-docker.sh
```

The script:

1. Discovers Compose stacks under `/opt/openalgo/<domain>/`
   (override with `INSTALL_BASE=/your/path` if you installed elsewhere)
2. Picks one if multiple exist (re-run for each instance)
3. Refuses if `FLASK_DEBUG=True` is set in the bind-mounted `.env`
4. Backs up the per-instance `.env`, then sets the same four MCP keys
5. `docker compose restart` for that instance — the container's
   `start.sh` runs `migrate_all.py` automatically before gunicorn
   comes back up, so schema changes apply
6. Probes the discovery / JWKS / healthz endpoints over the configured
   `MCP_PUBLIC_URL`

**Multi-instance**: re-run for each domain. Each instance gets its
own OAuth signing keys (under the per-container `keys/` volume), its
own DCR client list, its own audit log — they're fully isolated.

**Manual fallback** (if the helper doesn't fit your layout): edit the
bind-mounted `.env` for that instance and add:

```
MCP_HTTP_ENABLED = 'True'
MCP_PUBLIC_URL = 'https://yourdomain.com'
MCP_OAUTH_REQUIRE_APPROVAL = 'True'
MCP_OAUTH_WRITE_SCOPE_ENABLED = 'False'
MCP_HTTP_CORS_ORIGINS = 'https://claude.ai,https://chatgpt.com'
```

Then `cd /opt/openalgo/<domain> && docker compose restart`.

### Steps for fresh installs

The four install scripts in this folder don't yet ship with an
inline "enable MCP at install time?" prompt — that's a follow-up.
For now: run the appropriate enabler immediately after the install
script completes. The enablers handle everything else.

### What's NOT enabled by default

- **`write:orders` scope** — the `MCP_OAUTH_WRITE_SCOPE_ENABLED=False`
  default keeps order placement OFF even after the master switch is
  on. MCP starts read-only. Flip the env var only after reading the
  threat-model section below.
- **DCR auto-approval** — `MCP_OAUTH_REQUIRE_APPROVAL=True` means the
  admin must explicitly approve every newly registered MCP client
  before it can complete the OAuth dance.

---

## Mode 2 — Subdomain (defense-in-depth)

If you want the MCP surface on a separate hostname (e.g.
`mcp.yourdomain.com`) so its cookies, CORS, and TLS lifecycle are
isolated from the dashboard, the steps below are the manual recipe.
This is **not** automated — but it's the same pattern as the existing
`install/install-docker-multi-custom-ssl.sh` flow.

### Why bother

- A bug at `/mcp` cannot read dashboard session cookies
  (cookies are scoped to their original domain)
- Tighter, MCP-specific CORS allowlist on the subdomain
- TLS cert lifecycle for MCP can be rotated independently
- Easier to drop just the MCP surface (DNS or nginx) without affecting
  the dashboard

### What you need first

- An A or CNAME record for the MCP hostname pointing at the same
  server as your dashboard
- A working dashboard install via `install/install.sh`

### Steps

1. **Run the same-domain enable first** so the env vars and signing
   key are in place:

   ```bash
   sudo ./install/enable-remote-mcp.sh
   # Use https://mcp.yourdomain.com when prompted for MCP_PUBLIC_URL
   ```

2. **Edit the existing nginx config** (the file written by
   `install.sh`, typically `/etc/nginx/sites-available/yourdomain.com.conf`
   or `/etc/nginx/conf.d/yourdomain.com.conf`). Add a second
   `server { listen 443 ssl; ... }` block for the MCP hostname:

   ```nginx
   server {
       listen 443 ssl;
       listen [::]:443 ssl;
       server_name mcp.yourdomain.com;

       ssl_certificate /etc/letsencrypt/live/mcp.yourdomain.com/fullchain.pem;
       ssl_certificate_key /etc/letsencrypt/live/mcp.yourdomain.com/privkey.pem;
       ssl_protocols TLSv1.2 TLSv1.3;

       # Hardening
       add_header X-Content-Type-Options nosniff;
       add_header Strict-Transport-Security "max-age=63072000" always;
       # No CSP needed — we only serve JSON / SSE here.

       # Only forward the OAuth + MCP paths to Gunicorn. Everything
       # else 404s — keeps the dashboard surface invisible from this
       # hostname.
       location ^~ /.well-known/oauth-authorization-server {
           proxy_pass http://unix:/var/run/openalgo/<DEPLOY_NAME>.sock;
           proxy_set_header Host $host;
           proxy_set_header X-Forwarded-Proto $scheme;
       }
       location ^~ /.well-known/oauth-protected-resource {
           proxy_pass http://unix:/var/run/openalgo/<DEPLOY_NAME>.sock;
           proxy_set_header Host $host;
           proxy_set_header X-Forwarded-Proto $scheme;
       }
       location ^~ /oauth/ {
           proxy_pass http://unix:/var/run/openalgo/<DEPLOY_NAME>.sock;
           proxy_set_header Host $host;
           proxy_set_header X-Forwarded-Proto $scheme;
       }
       location = /mcp {
           proxy_pass http://unix:/var/run/openalgo/<DEPLOY_NAME>.sock;
           proxy_http_version 1.1;
           proxy_buffering off;
           proxy_read_timeout 300s;
           proxy_set_header Host $host;
           proxy_set_header X-Forwarded-Proto $scheme;
       }
       location ^~ /mcp/ {
           proxy_pass http://unix:/var/run/openalgo/<DEPLOY_NAME>.sock;
           proxy_http_version 1.1;
           proxy_buffering off;
           proxy_read_timeout 300s;
           proxy_set_header Host $host;
           proxy_set_header X-Forwarded-Proto $scheme;
       }

       location / { return 404; }
   }
   ```

   Replace `<DEPLOY_NAME>` with the value `install.sh` printed at
   end of run (typically `${DOMAIN/./-}-${BROKER}`).

3. **Issue a cert** for the new hostname:

   ```bash
   sudo certbot --nginx -d mcp.yourdomain.com --non-interactive \
       --agree-tos --email admin@yourdomain.com
   ```

4. **Reload nginx**:

   ```bash
   sudo nginx -t && sudo systemctl reload nginx
   ```

5. **Verify**:

   ```bash
   curl -s https://mcp.yourdomain.com/.well-known/oauth-authorization-server | jq
   curl -s -o /dev/null -w '%{http_code}\n' https://mcp.yourdomain.com/mcp/healthz
   ```

   The discovery JSON should advertise `mcp.yourdomain.com` URLs (it
   reads `MCP_PUBLIC_URL` from `.env`, which step 1 already set).

---

## Connecting a hosted MCP client (claude.ai)

1. In the client's MCP integration UI, point at:

   ```
   https://yourdomain.com/mcp     (or https://mcp.yourdomain.com/mcp)
   ```

2. The client probes the discovery endpoint, registers itself via DCR,
   and redirects you to OpenAlgo for OAuth approval.

3. **First-time approval gate** — because `MCP_OAUTH_REQUIRE_APPROVAL=True`,
   the new client lands in pending state and the OAuth flow refuses to
   complete until you approve. Approve via the admin console:

   - Sign in to OpenAlgo at `https://yourdomain.com`
   - Open **Admin → Remote MCP** (`/admin/remote-mcp`)
   - The new client appears in the **Pending approvals** card with the
     name the hosted client supplied (e.g. *"ChatGPT MCP Connector"*)
   - Verify the timestamp + name, then click **Approve**

   The same page also lists already-approved clients, the audit log
   over `log/mcp.jsonl`, and a **Kill switch** that revokes every
   refresh token across every approved client.

4. Sign in to your OpenAlgo dashboard if prompted, review the scopes,
   and click **Authorize**.

5. The client now has an access token and can call MCP tools. Watch
   `log/mcp.jsonl` (or the audit viewer in `/admin/remote-mcp`) to see
   every tool call audited.

## Operational tips

| Thing | Where |
|---|---|
| Audit log | `log/mcp.jsonl` (one JSON line per tool call) |
| Errors | `log/errors.jsonl` (write-tool pre-execution warnings show up here too) |
| Signing keys | `keys/mcp_oauth_<kid>.pem` (chmod 600) |
| OAuth client list | `sqlite3 db/openalgo.db 'SELECT * FROM oauth_clients'` |
| Active refresh tokens | `sqlite3 db/openalgo.db 'SELECT id, client_id, family_id, revoked_at FROM oauth_refresh_tokens'` |
| Kill switch (revoke everything) | `sqlite3 db/openalgo.db "UPDATE oauth_refresh_tokens SET revoked_at=CURRENT_TIMESTAMP WHERE revoked_at IS NULL"` |

## Threat model summary

(Full details in `docs/prd/remote-mcp.md`.)

| Defense | How |
|---|---|
| Stolen access token → unauthorized order | 15-min TTL; per-token rate limits; pre-write WARNING log; one-click kill switch |
| DCR abuse | Per-IP rate limit + admin approval default |
| Refresh token replay | Single-use rotation + family revocation on reuse |
| PKCE | S256 mandatory, `plain` not advertised |
| Open redirect | Exact `redirect_uri` match |
| CORS exfil | Strict allowlist (default: claude.ai, chatgpt.com) |
| Debug-mode token leak | Pre-flight RuntimeError if `FLASK_DEBUG=True` |
| Compromised signing key | `kid` rotation supported; one-window grace |
| Tool args leaking via logs | Audit log stores SHA-256 hash of args, not args themselves |

## Disabling

**Native Ubuntu** (`install.sh`, `install-multi.sh`):

```bash
# Edit the .env, set:
#   MCP_HTTP_ENABLED = 'False'
sudo systemctl restart openalgo-<deploy-name>
```

**Docker** (`install-docker.sh`, `install-docker-multi-custom-ssl.sh`):

```bash
# Edit the bind-mounted .env, set:
#   MCP_HTTP_ENABLED = 'False'
cd /opt/openalgo/<domain> && sudo docker compose restart
```

Either way, the OAuth and MCP routes immediately stop responding.
Existing access tokens hit 404 on the next request. Local stdio MCP
(Claude Desktop / Cursor / Windsurf) is completely unaffected — it
runs through `mcp/mcpserver.py` over stdin/stdout and doesn't touch
the HTTP transport at all.

For a softer takedown that keeps MCP enabled but revokes every active
session: visit `/admin/remote-mcp` on the dashboard and click **Kill
switch**. That sets `revoked_at` on every refresh token in the
database. Hosted clients are forced through a fresh OAuth dance the
next time they refresh.

```


---

# FILE: install\update.bat

```bat
@echo off
REM ============================================================================
REM OpenAlgo Update Script for Windows
REM ============================================================================
REM
REM Usage: update.bat
REM
REM This script updates OpenAlgo to the latest version using the UV method.
REM Run from the install\ directory or the openalgo project root.
REM
REM Prerequisites:
REM   - Python 3.12+
REM   - uv package manager (pip install uv)
REM   - Git
REM   - Node.js 20+ (optional, for frontend build)
REM
REM ============================================================================

setlocal enabledelayedexpansion

REM Banner
echo.
echo   ========================================
echo        OpenAlgo Update Script
echo        Windows Edition
echo   ========================================
echo.

REM Detect OpenAlgo directory
set "SCRIPT_DIR=%~dp0"
if "%SCRIPT_DIR:~-1%"=="\" set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"

REM Check if we're in the install\ directory or the project root
if exist "%SCRIPT_DIR%\app.py" (
    set "OPENALGO_DIR=%SCRIPT_DIR%"
) else if exist "%SCRIPT_DIR%\..\app.py" (
    pushd "%SCRIPT_DIR%\.."
    set "OPENALGO_DIR=!CD!"
    popd
) else (
    REM Try current directory
    if exist "app.py" (
        set "OPENALGO_DIR=%CD%"
    ) else (
        echo [ERROR] Could not find OpenAlgo directory.
        echo.
        echo Please run this script from:
        echo   - The openalgo project root directory, OR
        echo   - The install\ directory within openalgo
        echo.
        pause
        exit /b 1
    )
)

echo [INFO] OpenAlgo directory: %OPENALGO_DIR%
echo.

REM Verify git repository
if not exist "%OPENALGO_DIR%\.git" (
    echo [ERROR] Not a git repository: %OPENALGO_DIR%
    echo Please ensure OpenAlgo was installed via git clone.
    echo.
    pause
    exit /b 1
)

REM Check prerequisites
echo [INFO] Checking prerequisites...

where git >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Git is not installed or not in PATH.
    echo Download from: https://git-scm.com/download/win
    pause
    exit /b 1
)
echo   [OK] Git found

where python >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH.
    echo Download from: https://www.python.org/downloads/
    pause
    exit /b 1
)
echo   [OK] Python found

REM Check for uv
set "UV_CMD="
where uv >nul 2>&1
if not errorlevel 1 (
    set "UV_CMD=uv"
    echo   [OK] uv found (standalone)
) else (
    python -m uv --version >nul 2>&1
    if not errorlevel 1 (
        set "UV_CMD=python -m uv"
        echo   [OK] uv found (Python module)
    ) else (
        echo [ERROR] uv is not installed.
        echo Install with: pip install uv
        echo.
        pause
        exit /b 1
    )
)
echo.

REM Get current version
pushd "%OPENALGO_DIR%"

for /f "tokens=*" %%i in ('git rev-parse --short HEAD 2^>nul') do set "CURRENT_COMMIT=%%i"
for /f "tokens=*" %%i in ('git branch --show-current 2^>nul') do set "CURRENT_BRANCH=%%i"
if "%CURRENT_BRANCH%"=="" set "CURRENT_BRANCH=main"

echo [INFO] Current version: %CURRENT_COMMIT% (branch: %CURRENT_BRANCH%)
echo.

REM Generate timestamp for backups
for /f "tokens=2 delims==" %%i in ('wmic os get localdatetime /value 2^>nul ^| findstr LocalDateTime') do set "DT=%%i"
set "TIMESTAMP=%DT:~0,8%_%DT:~8,6%"

REM ========================================
REM Step 1: Backup databases
REM ========================================
echo [Step 1/5] Backing up databases...

set "BACKUP_DIR=%OPENALGO_DIR%\db\backup_%TIMESTAMP%"
set "BACKUP_COUNT=0"

if exist "%OPENALGO_DIR%\db\" (
    md "%BACKUP_DIR%" 2>nul

    for %%f in (openalgo.db logs.db latency.db sandbox.db) do (
        if exist "%OPENALGO_DIR%\db\%%f" (
            copy /y "%OPENALGO_DIR%\db\%%f" "%BACKUP_DIR%\%%f" >nul 2>&1
            echo   Backed up: %%f
            set /a BACKUP_COUNT+=1
        )
    )

    if exist "%OPENALGO_DIR%\db\historify.duckdb" (
        copy /y "%OPENALGO_DIR%\db\historify.duckdb" "%BACKUP_DIR%\historify.duckdb" >nul 2>&1
        echo   Backed up: historify.duckdb
        set /a BACKUP_COUNT+=1
    )

    if !BACKUP_COUNT! EQU 0 (
        echo   No databases found to backup (fresh installation)
        rd "%BACKUP_DIR%" 2>nul
    ) else (
        echo   [OK] Backup location: %BACKUP_DIR%
    )
) else (
    echo   No database directory found (fresh installation)
)
echo.

REM ========================================
REM Step 2: Pull latest code
REM ========================================
echo [Step 2/5] Pulling latest code...

REM Check for local modifications
set "HAS_CHANGES="
for /f "tokens=*" %%i in ('git status --porcelain 2^>nul ^| findstr /v "^??"') do (
    set "HAS_CHANGES=1"
)

set "STASHED="
if defined HAS_CHANGES (
    echo   Local modifications detected. Stashing changes...
    git stash push -m "auto-stash before update %TIMESTAMP%"
    set "STASHED=1"
)

git pull origin %CURRENT_BRANCH%
if errorlevel 1 (
    echo.
    echo [ERROR] Failed to pull latest code.
    echo Please resolve any git conflicts and try again.
    if defined STASHED (
        echo Note: Your changes are stashed. Run 'git stash pop' to restore.
    )
    popd
    pause
    exit /b 1
)

for /f "tokens=*" %%i in ('git rev-parse --short HEAD 2^>nul') do set "NEW_COMMIT=%%i"

if "%CURRENT_COMMIT%"=="%NEW_COMMIT%" (
    echo   [OK] Already up to date (%CURRENT_COMMIT%)
) else (
    echo   [OK] Updated: %CURRENT_COMMIT% -^> %NEW_COMMIT%
)

if defined STASHED (
    echo   [NOTE] Local changes were stashed. Use 'git stash pop' to restore.
)
echo.

REM ========================================
REM Step 3: Check environment configuration
REM ========================================
echo [Step 3/5] Checking environment configuration...

if not exist "%OPENALGO_DIR%\.env" (
    echo   [WARNING] No .env file found. Creating from .sample.env...
    if exist "%OPENALGO_DIR%\.sample.env" (
        copy /y "%OPENALGO_DIR%\.sample.env" "%OPENALGO_DIR%\.env" >nul

        REM Generate fresh APP_KEY and API_KEY_PEPPER. Without this, the new .env
        REM would carry the public sample placeholders — the app's startup check
        REM would then auto-rotate them, but generating here keeps update.bat
        REM symmetric with the other install scripts.
        for /f %%i in ('python -c "import secrets; print(secrets.token_hex(32))"') do set NEW_APP_KEY=%%i
        for /f %%i in ('python -c "import secrets; print(secrets.token_hex(32))"') do set NEW_PEPPER=%%i
        powershell -Command "(Get-Content '%OPENALGO_DIR%\.env') -replace 'OPENALGO_PLACEHOLDER_APP_KEY_REGENERATE_BEFORE_USE', '!NEW_APP_KEY!' | Set-Content '%OPENALGO_DIR%\.env'"
        powershell -Command "(Get-Content '%OPENALGO_DIR%\.env') -replace 'OPENALGO_PLACEHOLDER_API_KEY_PEPPER_REGENERATE_BEFORE_USE', '!NEW_PEPPER!' | Set-Content '%OPENALGO_DIR%\.env'"
        echo   [OK] Generated fresh APP_KEY and API_KEY_PEPPER in .env

        echo   [ACTION REQUIRED] Please edit .env with your broker credentials and settings.
    ) else (
        echo   [ERROR] .sample.env not found. Cannot create .env.
    )
) else (
    echo   [OK] Environment file exists.
    echo   Review .sample.env for any new variables added in this update.
)
echo.

REM ========================================
REM Step 4: Update Python dependencies
REM ========================================
echo [Step 4/5] Updating Python dependencies with uv...

%UV_CMD% sync
if errorlevel 1 (
    echo.
    echo [ERROR] Failed to update Python dependencies.
    echo Try running manually: uv sync
    popd
    pause
    exit /b 1
)

echo   [OK] Dependencies updated successfully.
echo.

REM ========================================
REM Step 5: Run database migrations
REM ========================================
echo [Step 5/5] Running database migrations...

if exist "%OPENALGO_DIR%\upgrade\migrate_all.py" (
    %UV_CMD% run upgrade/migrate_all.py
    if errorlevel 1 (
        echo   [WARNING] Some migrations may have had issues. Check output above.
    ) else (
        echo   [OK] Database migrations completed.
    )
) else (
    echo   [WARNING] No migration script found (upgrade\migrate_all.py)
)
echo.

REM ========================================
REM Build frontend if needed
REM ========================================
if not exist "%OPENALGO_DIR%\frontend\dist\" (
    where npm >nul 2>&1
    if not errorlevel 1 (
        echo [OPTIONAL] Building React frontend (dist\ not found)...
        pushd "%OPENALGO_DIR%\frontend"
        call npm install
        call npm run build
        if errorlevel 1 (
            echo   [WARNING] Frontend build failed.
            echo   Run manually: cd frontend ^&^& npm install ^&^& npm run build
        ) else (
            echo   [OK] Frontend built successfully.
        )
        popd
    ) else (
        echo [NOTE] frontend\dist\ not found and Node.js is not installed.
        echo   Install Node.js and run: cd frontend ^&^& npm install ^&^& npm run build
    )
    echo.
)

REM ========================================
REM Summary
REM ========================================
echo.
echo   ========================================
echo   OpenAlgo Update Complete!
echo   ========================================
echo.
echo   Version:   %CURRENT_COMMIT% -^> %NEW_COMMIT%
echo   Branch:    %CURRENT_BRANCH%
echo   Directory: %OPENALGO_DIR%
if exist "%BACKUP_DIR%\" (
    echo   Backup:    %BACKUP_DIR%
)
echo.
echo   Next Steps:
echo     Start application: uv run app.py
echo     API documentation: http://127.0.0.1:5000/api/docs
echo.

if defined STASHED (
    echo   Reminder: Local changes were stashed. Use 'git stash pop' to restore.
    echo.
)

popd
pause
exit /b 0

```


---

# FILE: install\update.sh

```sh
#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# OpenAlgo Update Banner
echo -e "${BLUE}"
echo "  ██████╗ ██████╗ ███████╗███╗   ██╗ █████╗ ██╗      ██████╗  ██████╗ "
echo " ██╔═══██╗██╔══██╗██╔════╝████╗  ██║██╔══██╗██║     ██╔════╝ ██╔═══██╗"
echo " ██║   ██║██████╔╝███████╗██╔██╗ ██║███████║██║     ██║  ███╗██║   ██║"
echo " ██║   ██║██╔═══╝ ██╔══╝  ██║╚██╗██║██╔══██║██║     ██║   ██║██║   ██║"
echo " ╚██████╔╝██╗     ███████╗██║ ╚████║██║  ██║███████╗╚██████╔╝╚██████╔╝"
echo "  ╚═════╝ ╚═╝     ╚══════╝╚═╝  ╚═══╝╚═╝  ╚═╝╚══════╝ ╚═════╝  ╚═════╝ "
echo "                          UPDATE  SCRIPT                                "
echo -e "${NC}"

# OpenAlgo Update Script
# Updates an existing OpenAlgo installation to the latest version using the UV method.
# Supports both server deployments (installed via install.sh) and local development setups.

# Create logs directory if it doesn't exist
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
LOGS_DIR="$SCRIPT_DIR/logs"
mkdir -p "$LOGS_DIR"

# Generate unique log file name
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_FILE="$LOGS_DIR/update_${TIMESTAMP}.log"

# Function to log messages to both console and log file
log_message() {
    local message="$1"
    local color="$2"
    echo -e "${color}${message}${NC}" | tee -a "$LOG_FILE"
}

# Function to check if command was successful
check_status() {
    if [ $? -ne 0 ]; then
        log_message "Error: $1" "$RED"
        exit 1
    fi
}

# Start logging
log_message "Starting OpenAlgo update log at: $LOG_FILE" "$BLUE"
log_message "----------------------------------------" "$BLUE"

# Detect OS type
OS_TYPE=$(grep -w "ID" /etc/os-release | cut -d "=" -f 2 | tr -d '"')

# Handle OS variants - map to base distributions
case "$OS_TYPE" in
    "pop"|"linuxmint"|"zorin")
        OS_TYPE="ubuntu"
        ;;
    "manjaro"|"manjaro-arm"|"endeavouros"|"cachyos")
        OS_TYPE="arch"
        ;;
    "rocky"|"almalinux"|"ol")
        OS_TYPE="rhel"
        ;;
esac

# Detect web server user and Python command based on OS
case "$OS_TYPE" in
    ubuntu|debian|raspbian)
        WEB_USER="www-data"
        WEB_GROUP="www-data"
        PYTHON_CMD="python3"
        ;;
    centos|fedora|rhel|amzn)
        WEB_USER="nginx"
        WEB_GROUP="nginx"
        PYTHON_CMD="python3"
        ;;
    arch)
        WEB_USER="http"
        WEB_GROUP="http"
        PYTHON_CMD="python"
        ;;
    *)
        log_message "Warning: Unrecognized OS ($OS_TYPE). Defaulting to python3." "$YELLOW"
        WEB_USER="www-data"
        WEB_GROUP="www-data"
        PYTHON_CMD="python3"
        ;;
esac

log_message "Detected OS: $OS_TYPE" "$BLUE"
log_message "Python command: $PYTHON_CMD" "$BLUE"

# Detect uv command
detect_uv() {
    if command -v uv >/dev/null 2>&1; then
        UV_CMD="uv"
    elif $PYTHON_CMD -m uv --version >/dev/null 2>&1; then
        UV_CMD="$PYTHON_CMD -m uv"
    else
        log_message "Error: uv is not installed." "$RED"
        log_message "Install with: pip install uv" "$YELLOW"
        exit 1
    fi
    log_message "Using uv: $UV_CMD" "$GREEN"
}

# Find server deployments installed via install.sh
#
# Two layouts are supported:
#   1. Simple (current install.sh)   /var/python/openalgo, service "openalgo"
#   2. Legacy multi-deploy           /var/python/openalgo-flask/<deploy>/openalgo,
#                                    service "openalgo-<deploy>" (still produced
#                                    by install/install-multi.sh)
# We try the simple layout first because it's unambiguous; only fall back
# to scanning the legacy parent dir when the simple path is absent.
SIMPLE_PATH="/var/python/openalgo"
DEPLOY_BASE="/var/python/openalgo-flask"
SERVER_MODE=false
STASHED=false

find_deployments() {
    local deployments=()
    if [ -d "$DEPLOY_BASE" ]; then
        for dir in "$DEPLOY_BASE"/*/; do
            if [ -d "${dir}openalgo/.git" ]; then
                deploy_name=$(basename "$dir")
                deployments+=("$deploy_name")
            fi
        done
    fi
    echo "${deployments[@]}"
}

if [ -d "$SIMPLE_PATH/.git" ] && [ -f "$SIMPLE_PATH/.env" ]; then
    SERVER_MODE=true
    SELECTED_DEPLOY="openalgo"
    BASE_PATH="$SIMPLE_PATH"
    OPENALGO_PATH="$SIMPLE_PATH"
    VENV_PATH="$SIMPLE_PATH/.venv"
    SERVICE_NAME="openalgo"

    log_message "Found OpenAlgo install at $SIMPLE_PATH" "$GREEN"
    log_message "Service: $SERVICE_NAME" "$BLUE"
else
    DEPLOYMENTS=($(find_deployments))
fi

if [ "$SERVER_MODE" = false ] && [ ${#DEPLOYMENTS[@]} -gt 0 ]; then
    SERVER_MODE=true
    log_message "Found ${#DEPLOYMENTS[@]} legacy server deployment(s):" "$GREEN"

    for i in "${!DEPLOYMENTS[@]}"; do
        log_message "  $((i+1)). ${DEPLOYMENTS[$i]}" "$BLUE"
    done

    if [ ${#DEPLOYMENTS[@]} -eq 1 ]; then
        SELECTED_DEPLOY="${DEPLOYMENTS[0]}"
        log_message "\nAuto-selected: $SELECTED_DEPLOY" "$GREEN"
    else
        echo ""
        while true; do
            read -p "Select deployment to update (1-${#DEPLOYMENTS[@]}): " choice
            if [[ "$choice" =~ ^[0-9]+$ ]] && [ "$choice" -ge 1 ] && [ "$choice" -le ${#DEPLOYMENTS[@]} ]; then
                SELECTED_DEPLOY="${DEPLOYMENTS[$((choice-1))]}"
                break
            else
                log_message "Invalid choice. Please enter a number between 1 and ${#DEPLOYMENTS[@]}." "$RED"
            fi
        done
    fi

    # Derive paths from deployment name (legacy multi-deploy layout)
    BASE_PATH="$DEPLOY_BASE/$SELECTED_DEPLOY"
    OPENALGO_PATH="$BASE_PATH/openalgo"
    VENV_PATH="$BASE_PATH/venv"
    SERVICE_NAME="openalgo-$SELECTED_DEPLOY"

    log_message "\nUpdating deployment: $SELECTED_DEPLOY" "$BLUE"
    log_message "Path: $OPENALGO_PATH" "$BLUE"
    log_message "Service: $SERVICE_NAME" "$BLUE"
fi

if [ "$SERVER_MODE" = false ]; then
    # Check if we're in or near an openalgo git repo (local development)
    if [ -d ".git" ] && [ -f "app.py" ]; then
        OPENALGO_PATH="$(pwd)"
    elif [ -d "$SCRIPT_DIR/../.git" ] && [ -f "$SCRIPT_DIR/../app.py" ]; then
        OPENALGO_PATH="$(cd "$SCRIPT_DIR/.." && pwd)"
    else
        log_message "Error: No OpenAlgo deployment found." "$RED"
        log_message "For server deployments, ensure install.sh was run first." "$YELLOW"
        log_message "For local development, run this script from the openalgo directory." "$YELLOW"
        exit 1
    fi

    log_message "Detected local development setup at: $OPENALGO_PATH" "$GREEN"
fi

# Detect uv
detect_uv

# Get current version info before update
cd "$OPENALGO_PATH"
if [ "$SERVER_MODE" = true ]; then
    CURRENT_COMMIT=$(sudo git -C "$OPENALGO_PATH" rev-parse --short HEAD 2>/dev/null || echo "unknown")
    CURRENT_BRANCH=$(sudo git -C "$OPENALGO_PATH" branch --show-current 2>/dev/null || echo "main")
else
    CURRENT_COMMIT=$(git rev-parse --short HEAD 2>/dev/null || echo "unknown")
    CURRENT_BRANCH=$(git branch --show-current 2>/dev/null || echo "main")
fi
log_message "\nCurrent version: $CURRENT_COMMIT (branch: $CURRENT_BRANCH)" "$BLUE"

# ============================================
# Step 1: Stop service (server mode only)
# ============================================
if [ "$SERVER_MODE" = true ]; then
    log_message "\n[Step 1/7] Stopping service: $SERVICE_NAME..." "$BLUE"
    if sudo systemctl is-active --quiet "$SERVICE_NAME" 2>/dev/null; then
        sudo systemctl stop "$SERVICE_NAME"
        check_status "Failed to stop $SERVICE_NAME"
        log_message "Service stopped successfully" "$GREEN"
    else
        log_message "Service is not currently running" "$YELLOW"
    fi
else
    log_message "\n[Step 1/7] Skipping service stop (local development mode)" "$BLUE"
fi

# ============================================
# Step 2: Backup databases
# ============================================
log_message "\n[Step 2/7] Backing up databases..." "$BLUE"
BACKUP_DIR="$OPENALGO_PATH/db/backup_${TIMESTAMP}"
BACKUP_COUNT=0

if [ -d "$OPENALGO_PATH/db" ]; then
    if [ "$SERVER_MODE" = true ]; then
        sudo mkdir -p "$BACKUP_DIR"
    else
        mkdir -p "$BACKUP_DIR"
    fi

    # Backup SQLite databases
    for db_file in openalgo.db logs.db latency.db sandbox.db; do
        if [ -f "$OPENALGO_PATH/db/$db_file" ]; then
            if [ "$SERVER_MODE" = true ]; then
                sudo cp "$OPENALGO_PATH/db/$db_file" "$BACKUP_DIR/$db_file"
            else
                cp "$OPENALGO_PATH/db/$db_file" "$BACKUP_DIR/$db_file"
            fi
            log_message "  Backed up: $db_file" "$GREEN"
            BACKUP_COUNT=$((BACKUP_COUNT + 1))
        fi
    done

    # Backup DuckDB database
    if [ -f "$OPENALGO_PATH/db/historify.duckdb" ]; then
        if [ "$SERVER_MODE" = true ]; then
            sudo cp "$OPENALGO_PATH/db/historify.duckdb" "$BACKUP_DIR/historify.duckdb"
        else
            cp "$OPENALGO_PATH/db/historify.duckdb" "$BACKUP_DIR/historify.duckdb"
        fi
        log_message "  Backed up: historify.duckdb" "$GREEN"
        BACKUP_COUNT=$((BACKUP_COUNT + 1))
    fi

    if [ $BACKUP_COUNT -eq 0 ]; then
        log_message "  No databases found to backup (fresh installation)" "$YELLOW"
        if [ "$SERVER_MODE" = true ]; then
            sudo rmdir "$BACKUP_DIR" 2>/dev/null
        else
            rmdir "$BACKUP_DIR" 2>/dev/null
        fi
    else
        log_message "  Backup location: $BACKUP_DIR ($BACKUP_COUNT files)" "$GREEN"
    fi
else
    log_message "  No database directory found (fresh installation)" "$YELLOW"
fi

# ============================================
# Step 3: Pull latest code
# ============================================
log_message "\n[Step 3/7] Pulling latest code from repository..." "$BLUE"
cd "$OPENALGO_PATH"

# Check for local modifications (excluding untracked files)
if [ "$SERVER_MODE" = true ]; then
    LOCAL_CHANGES=$(sudo git -C "$OPENALGO_PATH" status --porcelain 2>/dev/null | grep -v "^??" | head -20)
else
    LOCAL_CHANGES=$(git status --porcelain 2>/dev/null | grep -v "^??" | head -20)
fi

if [ -n "$LOCAL_CHANGES" ]; then
    log_message "Local modifications detected:" "$YELLOW"
    echo "$LOCAL_CHANGES" | tee -a "$LOG_FILE"
    log_message "\nStashing local changes..." "$YELLOW"
    if [ "$SERVER_MODE" = true ]; then
        sudo git -C "$OPENALGO_PATH" stash push -m "auto-stash before update $TIMESTAMP"
    else
        git stash push -m "auto-stash before update $TIMESTAMP"
    fi
    STASHED=true
fi

# Pull latest code
if [ "$SERVER_MODE" = true ]; then
    sudo git -C "$OPENALGO_PATH" pull origin "$CURRENT_BRANCH"
else
    git pull origin "$CURRENT_BRANCH"
fi
check_status "Failed to pull latest code. Please resolve any conflicts and try again"

# Get new commit hash
if [ "$SERVER_MODE" = true ]; then
    NEW_COMMIT=$(sudo git -C "$OPENALGO_PATH" rev-parse --short HEAD 2>/dev/null || echo "unknown")
else
    NEW_COMMIT=$(git rev-parse --short HEAD 2>/dev/null || echo "unknown")
fi

if [ "$CURRENT_COMMIT" = "$NEW_COMMIT" ]; then
    log_message "Already up to date ($CURRENT_COMMIT)" "$GREEN"
else
    log_message "Updated: $CURRENT_COMMIT -> $NEW_COMMIT" "$GREEN"
fi

if [ "$STASHED" = true ]; then
    log_message "Note: Local changes were stashed. Use 'git stash pop' to restore if needed." "$YELLOW"
fi

# ============================================
# Step 4: Check environment configuration
# ============================================
log_message "\n[Step 4/7] Checking environment configuration..." "$BLUE"

if [ -f "$OPENALGO_PATH/.env" ] && [ -f "$OPENALGO_PATH/.sample.env" ]; then
    # Extract variable names from both files and compare
    SAMPLE_VARS=$(grep -oP "^[A-Z_][A-Z_0-9]+ *=" "$OPENALGO_PATH/.sample.env" 2>/dev/null | sed 's/ *=$//' | sort -u)
    CURRENT_VARS=$(grep -oP "^[A-Z_][A-Z_0-9]+ *=" "$OPENALGO_PATH/.env" 2>/dev/null | sed 's/ *=$//' | sort -u)

    NEW_VARS=$(comm -23 <(echo "$SAMPLE_VARS") <(echo "$CURRENT_VARS") 2>/dev/null)

    if [ -n "$NEW_VARS" ]; then
        log_message "New environment variables found in .sample.env:" "$YELLOW"
        while IFS= read -r var; do
            [ -n "$var" ] && log_message "  + $var" "$YELLOW"
        done <<< "$NEW_VARS"
        log_message "Please review .sample.env and add these to your .env if needed." "$YELLOW"
    else
        log_message "Environment configuration is up to date" "$GREEN"
    fi
elif [ ! -f "$OPENALGO_PATH/.env" ]; then
    log_message "Warning: No .env file found. Creating from .sample.env..." "$YELLOW"
    if [ "$SERVER_MODE" = true ]; then
        sudo cp "$OPENALGO_PATH/.sample.env" "$OPENALGO_PATH/.env"
    else
        cp "$OPENALGO_PATH/.sample.env" "$OPENALGO_PATH/.env"
    fi

    # Generate fresh APP_KEY and API_KEY_PEPPER and substitute the placeholders.
    # Without this, the new .env would carry the public sample placeholder values
    # — the app's startup check would then auto-rotate them, which works, but
    # generating here keeps update.sh symmetric with install.sh and avoids the
    # noisy "first-run setup" message after what the user thinks is just an update.
    NEW_APP_KEY=$($PYTHON_CMD -c "import secrets; print(secrets.token_hex(32))")
    NEW_PEPPER=$($PYTHON_CMD -c "import secrets; print(secrets.token_hex(32))")
    if [ "$SERVER_MODE" = true ]; then
        sudo sed -i "s|OPENALGO_PLACEHOLDER_APP_KEY_REGENERATE_BEFORE_USE|$NEW_APP_KEY|g" "$OPENALGO_PATH/.env"
        sudo sed -i "s|OPENALGO_PLACEHOLDER_API_KEY_PEPPER_REGENERATE_BEFORE_USE|$NEW_PEPPER|g" "$OPENALGO_PATH/.env"
        sudo chmod 600 "$OPENALGO_PATH/.env"
    else
        sed -i.bak "s|OPENALGO_PLACEHOLDER_APP_KEY_REGENERATE_BEFORE_USE|$NEW_APP_KEY|g" "$OPENALGO_PATH/.env" && rm -f "$OPENALGO_PATH/.env.bak"
        sed -i.bak "s|OPENALGO_PLACEHOLDER_API_KEY_PEPPER_REGENERATE_BEFORE_USE|$NEW_PEPPER|g" "$OPENALGO_PATH/.env" && rm -f "$OPENALGO_PATH/.env.bak"
        chmod 600 "$OPENALGO_PATH/.env"
    fi
    log_message "Generated fresh APP_KEY and API_KEY_PEPPER in $OPENALGO_PATH/.env" "$GREEN"
    log_message "Please edit $OPENALGO_PATH/.env with your broker credentials and settings." "$RED"
fi

# ============================================
# Step 4b: Existing-install hardening
# ============================================
# Two one-time fixups for deployments that predate the v2.0.0.6 security
# release: they may carry world-readable .env perms (the old install.sh did
# `chmod -R 755`) and they don't have TRUST_PROXY_HEADERS set so the
# default-secure value of FALSE would silently disable IP-based features
# behind their nginx proxy.
if [ -f "$OPENALGO_PATH/.env" ]; then
    # Tighten .env to mode 0o600 if it isn't already (server mode only —
    # the file is owned by the web user and gunicorn runs as that user, so
    # owner-only read is correct).
    if [ "$SERVER_MODE" = true ]; then
        ENV_PERMS=$(stat -c '%a' "$OPENALGO_PATH/.env" 2>/dev/null || stat -f '%Lp' "$OPENALGO_PATH/.env" 2>/dev/null)
        if [ "$ENV_PERMS" != "600" ]; then
            sudo chmod 600 "$OPENALGO_PATH/.env"
            log_message "Tightened .env perms: $ENV_PERMS -> 600 (owner-only)" "$GREEN"
        fi
    fi

    # Add TRUST_PROXY_HEADERS to .env if missing. Auto-detect whether nginx
    # is configured for this deployment so the default matches reality.
    if ! grep -q "^TRUST_PROXY_HEADERS" "$OPENALGO_PATH/.env"; then
        # Detect nginx in front of openalgo: any sites-enabled/ or conf.d/
        # config that mentions a unix-socket proxy_pass or the deployment name.
        BEHIND_NGINX="false"
        if [ -d /etc/nginx/sites-enabled ]; then
            if find /etc/nginx/sites-enabled -type f -o -type l 2>/dev/null | xargs grep -l "unix:.*\.sock\|openalgo\|gunicorn" 2>/dev/null | head -1 | grep -q .; then
                BEHIND_NGINX="true"
            fi
        fi
        if [ "$BEHIND_NGINX" = "false" ] && [ -d /etc/nginx/conf.d ]; then
            if find /etc/nginx/conf.d -type f -name "*.conf" 2>/dev/null | xargs grep -l "unix:.*\.sock\|openalgo\|gunicorn" 2>/dev/null | head -1 | grep -q .; then
                BEHIND_NGINX="true"
            fi
        fi
        if [ "$BEHIND_NGINX" = "true" ]; then
            echo "" | sudo tee -a "$OPENALGO_PATH/.env" >/dev/null
            echo "# Auto-added by update.sh — nginx reverse proxy detected." | sudo tee -a "$OPENALGO_PATH/.env" >/dev/null
            echo "TRUST_PROXY_HEADERS = 'TRUE'" | sudo tee -a "$OPENALGO_PATH/.env" >/dev/null
            log_message "Added TRUST_PROXY_HEADERS=TRUE to .env (nginx reverse proxy detected)" "$GREEN"
        else
            echo "" | sudo tee -a "$OPENALGO_PATH/.env" >/dev/null
            echo "# Auto-added by update.sh — set to TRUE only if behind a reverse proxy" | sudo tee -a "$OPENALGO_PATH/.env" >/dev/null
            echo "# that strips client-supplied X-Forwarded-For / CF-Connecting-IP / X-Real-IP." | sudo tee -a "$OPENALGO_PATH/.env" >/dev/null
            echo "TRUST_PROXY_HEADERS = 'FALSE'" | sudo tee -a "$OPENALGO_PATH/.env" >/dev/null
            log_message "Added TRUST_PROXY_HEADERS=FALSE to .env (no proxy detected)" "$YELLOW"
        fi
    fi
fi

# ============================================
# Step 5: Update Python dependencies
# ============================================
log_message "\n[Step 5/7] Updating Python dependencies..." "$BLUE"

if [ "$SERVER_MODE" = true ]; then
    # Server mode: use uv pip install with the deployment venv
    sudo $UV_CMD pip install --python "$VENV_PATH/bin/python" -r "$OPENALGO_PATH/requirements-nginx.txt"
    check_status "Failed to update Python dependencies"

    # Ensure gunicorn and eventlet are installed
    ACTIVATE_CMD="source $VENV_PATH/bin/activate"
    if ! sudo bash -c "$ACTIVATE_CMD && pip freeze | grep -q 'gunicorn=='"; then
        log_message "  Installing gunicorn..." "$YELLOW"
        sudo $UV_CMD pip install --python "$VENV_PATH/bin/python" "gunicorn>=25.0,<26"
    fi
    if ! sudo bash -c "$ACTIVATE_CMD && pip freeze | grep -q 'eventlet=='"; then
        log_message "  Installing eventlet..." "$YELLOW"
        sudo $UV_CMD pip install --python "$VENV_PATH/bin/python" eventlet
    fi
else
    # Local mode: use uv sync (reads pyproject.toml)
    cd "$OPENALGO_PATH"
    $UV_CMD sync
    check_status "Failed to update Python dependencies"
fi

log_message "Dependencies updated successfully" "$GREEN"

# ============================================
# Step 6: Set permissions (server mode) and run database migrations
# ============================================
if [ "$SERVER_MODE" = true ]; then
    log_message "\n[Step 6/7] Setting permissions and running database migrations..." "$BLUE"

    # Fix ownership and permissions before running migrations
    sudo chown -R "$WEB_USER:$WEB_GROUP" "$BASE_PATH"
    sudo chmod -R 755 "$BASE_PATH"

    # Ensure required directories exist with correct ownership
    sudo mkdir -p "$OPENALGO_PATH/db"
    sudo mkdir -p "$OPENALGO_PATH/tmp/numba_cache"
    sudo mkdir -p "$OPENALGO_PATH/tmp/matplotlib"
    sudo mkdir -p "$OPENALGO_PATH/strategies/scripts"
    sudo mkdir -p "$OPENALGO_PATH/strategies/examples"
    sudo mkdir -p "$OPENALGO_PATH/log/strategies"
    sudo mkdir -p "$OPENALGO_PATH/keys"
    sudo chown -R "$WEB_USER:$WEB_GROUP" "$OPENALGO_PATH"
    sudo chmod 700 "$OPENALGO_PATH/keys"

    log_message "Permissions set successfully" "$GREEN"

    # Run migrations as the web user (database files are owned by web user)
    if [ -f "$OPENALGO_PATH/upgrade/migrate_all.py" ]; then
        log_message "Running database migrations..." "$BLUE"
        sudo -u "$WEB_USER" bash -c "source $VENV_PATH/bin/activate && cd $OPENALGO_PATH && python upgrade/migrate_all.py" 2>&1 | tee -a "$LOG_FILE"
        if [ ${PIPESTATUS[0]} -ne 0 ]; then
            log_message "Retrying migrations with elevated permissions..." "$YELLOW"
            sudo bash -c "source $VENV_PATH/bin/activate && cd $OPENALGO_PATH && python upgrade/migrate_all.py" 2>&1 | tee -a "$LOG_FILE"
        fi
        log_message "Database migrations completed" "$GREEN"
    else
        log_message "No migration script found (upgrade/migrate_all.py)" "$YELLOW"
    fi
else
    log_message "\n[Step 6/7] Running database migrations..." "$BLUE"
    if [ -f "$OPENALGO_PATH/upgrade/migrate_all.py" ]; then
        cd "$OPENALGO_PATH"
        $UV_CMD run upgrade/migrate_all.py 2>&1 | tee -a "$LOG_FILE"
        log_message "Database migrations completed" "$GREEN"
    else
        log_message "No migration script found (upgrade/migrate_all.py)" "$YELLOW"
    fi
fi

# ============================================
# Step 7: Restart services (server mode) or finish (local mode)
# ============================================
if [ "$SERVER_MODE" = true ]; then
    log_message "\n[Step 7/7] Restarting services..." "$BLUE"

    # Reload systemd in case service file changed
    sudo systemctl daemon-reload

    # Start the OpenAlgo service
    sudo systemctl start "$SERVICE_NAME"
    check_status "Failed to start $SERVICE_NAME"

    # Reload Nginx
    sudo systemctl reload nginx
    check_status "Failed to reload Nginx"

    log_message "Services restarted successfully" "$GREEN"

    # Verify service is running
    sleep 3
    if sudo systemctl is-active --quiet "$SERVICE_NAME"; then
        log_message "Service $SERVICE_NAME is running" "$GREEN"
    else
        log_message "Warning: Service $SERVICE_NAME may not have started correctly" "$RED"
        log_message "Check logs with: sudo journalctl -u $SERVICE_NAME -n 50" "$YELLOW"
    fi
else
    log_message "\n[Step 7/7] Finalizing update..." "$BLUE"

    # Build frontend if dist/ directory is missing and npm is available
    if [ ! -d "$OPENALGO_PATH/frontend/dist" ]; then
        if command -v npm >/dev/null 2>&1; then
            log_message "Building React frontend (dist/ not found)..." "$BLUE"
            cd "$OPENALGO_PATH/frontend"
            npm install && npm run build
            if [ $? -eq 0 ]; then
                log_message "Frontend built successfully" "$GREEN"
            else
                log_message "Frontend build failed. Run manually: cd frontend && npm install && npm run build" "$YELLOW"
            fi
        else
            log_message "Warning: frontend/dist/ not found and Node.js is not installed." "$YELLOW"
            log_message "Install Node.js and run: cd frontend && npm install && npm run build" "$YELLOW"
        fi
    fi

    log_message "Update finalized" "$GREEN"
fi

# ============================================
# Summary
# ============================================
log_message "\n========================================" "$GREEN"
log_message "  OpenAlgo Update Summary" "$GREEN"
log_message "========================================" "$GREEN"
log_message "Version: $CURRENT_COMMIT -> $NEW_COMMIT" "$BLUE"
log_message "Branch: $CURRENT_BRANCH" "$BLUE"
log_message "Path: $OPENALGO_PATH" "$BLUE"
if [ -d "$BACKUP_DIR" ]; then
    log_message "Database Backup: $BACKUP_DIR" "$BLUE"
fi
if [ "$SERVER_MODE" = true ]; then
    log_message "Service: $SERVICE_NAME" "$BLUE"
    log_message "Mode: Server (Nginx + Gunicorn)" "$BLUE"
else
    log_message "Mode: Local Development" "$BLUE"
fi
log_message "Update Log: $LOG_FILE" "$BLUE"

if [ "$SERVER_MODE" = true ]; then
    log_message "\nUseful Commands:" "$YELLOW"
    log_message "  Check status:  sudo systemctl status $SERVICE_NAME" "$BLUE"
    log_message "  View logs:     sudo journalctl -u $SERVICE_NAME -n 50" "$BLUE"
    log_message "  Restart:       sudo systemctl restart $SERVICE_NAME" "$BLUE"
else
    log_message "\nNext Steps:" "$YELLOW"
    log_message "  Start application: uv run app.py" "$BLUE"
    log_message "  API documentation: http://127.0.0.1:5000/api/docs" "$BLUE"
fi

if [ -n "$NEW_VARS" ]; then
    log_message "\nReminder: New environment variables were found. Please review .sample.env." "$YELLOW"
fi

if [ "$STASHED" = true ]; then
    log_message "\nReminder: Local changes were stashed. Run 'git stash pop' to restore." "$YELLOW"
fi

log_message "\nUpdate completed successfully!" "$GREEN"

```
