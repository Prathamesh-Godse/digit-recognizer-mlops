# 06 · Nginx Reverse Proxy and HTTPS

*← [Index](../../INDEX.md) · [Server Deployment](../05-server-deployment/deployment.md)*

---

## What Nginx Does Here

The Docker container listens on `localhost:8000`. It is not directly exposed to the internet. Nginx acts as the public-facing gateway — it receives requests on ports 80 and 443, terminates SSL (or forwards to Cloudflare for termination), and proxies traffic inward to the container.

This is the same role Nginx plays for the WordPress server, just pointed at a different upstream.

---

## Step 1 — Verify Nginx is Installed

Nginx should already be on the server from the WordPress stack. Confirm:

```bash
nginx -v
sudo systemctl status nginx
```

If not installed:

```bash
sudo apt update
sudo apt install -y nginx
sudo systemctl enable nginx
sudo systemctl start nginx
```

---

## Step 2 — Create the Server Block

Create a new configuration file for the ML API:

```bash
sudo nano /etc/nginx/sites-available/digit-api
```

Paste the following configuration:

```nginx
server {
    listen 80;
    server_name api.yourdomain.com;

    # ── Redirect HTTP to HTTPS ────────────────────────────────────────── #
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl;
    server_name api.yourdomain.com;

    # ── SSL certificate paths (Certbot or Cloudflare Origin) ─────────── #
    ssl_certificate     /etc/ssl/certs/digit-api.crt;
    ssl_certificate_key /etc/ssl/private/digit-api.key;

    # ── SSL hardening (reuse from WordPress config if already present) ── #
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers on;
    ssl_ciphers 'ECDH+AESGCM:ECDH+AES256:ECDH+AES128:!aNULL:!MD5:!DSS';

    # ── Security headers ──────────────────────────────────────────────── #
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # ── Logging ───────────────────────────────────────────────────────── #
    access_log /var/log/nginx/digit-api.access.log;
    error_log  /var/log/nginx/digit-api.error.log;

    # ── Reverse proxy to Docker container ────────────────────────────── #
    location / {
        proxy_pass         http://localhost:8000;
        proxy_http_version 1.1;

        # Forward real client IP to FastAPI
        proxy_set_header   Host              $host;
        proxy_set_header   X-Real-IP         $remote_addr;
        proxy_set_header   X-Forwarded-For   $proxy_add_x_forwarded_for;
        proxy_set_header   X-Forwarded-Proto $scheme;

        # Timeouts — model inference is fast, but be generous
        proxy_connect_timeout 10s;
        proxy_read_timeout    30s;
        proxy_send_timeout    10s;
    }
}
```

Replace `api.yourdomain.com` with the actual subdomain or domain being used.

---

## Step 3 — Enable the Site

```bash
# Create the symlink to enable the site
sudo ln -s /etc/nginx/sites-available/digit-api \
           /etc/nginx/sites-enabled/digit-api

# Test the configuration syntax
sudo nginx -t

# Reload Nginx to apply changes (no downtime)
sudo systemctl reload nginx
```

If `nginx -t` reports any errors, fix them before reloading. Common issues: a typo in the file path, a missing semicolon, or `server_name` not matching the certificate's CN.

---

## Step 4 — Enable HTTPS

### Option A — Cloudflare (Recommended)

This setup mirrors the WordPress deployment. Cloudflare handles SSL termination between the client and Cloudflare's edge. Between Cloudflare and the origin server, Cloudflare uses an origin certificate.

**In the Cloudflare dashboard:**

1. Go to SSL/TLS → Overview → Set mode to **Full (strict)**
2. Go to SSL/TLS → Origin Server → Create Certificate
3. Download the `.pem` (certificate) and `.key` (private key) files

**On the server:**

```bash
sudo cp origin.pem /etc/ssl/certs/digit-api.crt
sudo cp origin.key /etc/ssl/private/digit-api.key
sudo chmod 600 /etc/ssl/private/digit-api.key
```

Update the Nginx config paths if needed, then reload:

```bash
sudo nginx -t && sudo systemctl reload nginx
```

**In the Cloudflare dashboard:**

4. DNS → Add an A record pointing `api.yourdomain.com` to the server IP
5. Make sure the proxy (orange cloud) is enabled

---

### Option B — Certbot / Let's Encrypt

If not using Cloudflare, obtain a certificate directly from Let's Encrypt:

```bash
sudo apt install -y certbot python3-certbot-nginx

# Obtain and install the certificate
sudo certbot --nginx -d api.yourdomain.com

# Verify auto-renewal is configured
sudo certbot renew --dry-run
```

Certbot will automatically modify the Nginx config to point to the new certificate files and set up a cron job for renewal.

---

## Step 5 — Test the HTTPS Endpoint

From a local machine (not the server):

```bash
# Health check
curl https://api.yourdomain.com/

# Predict (with a flat pixel array)
curl -X POST https://api.yourdomain.com/predict \
  -H "Content-Type: application/json" \
  -d '{"pixels": ['"$(python3 -c "print(','.join(['0.0']*784))"')"']}'
```

Also test via the browser: `https://api.yourdomain.com/docs` — the Swagger UI should load with a valid certificate and no browser warnings.

---

## Nginx Configuration Notes

### `proxy_pass http://localhost:8000`

This is the core reverse proxy directive. All incoming requests to the Nginx location block are forwarded to the Docker container's port on localhost. The container is not reachable from the internet directly.

### `proxy_set_header X-Real-IP`

Without this header, FastAPI sees every request coming from `127.0.0.1` (Nginx itself), which makes the prediction logs useless for tracking traffic. This header passes the real client IP through to the application.

### `proxy_read_timeout 30s`

FastAPI inference on a NumPy model is typically under 5ms. The 30-second timeout is generous — it exists to handle edge cases like a cold start where the model is loading from disk.

---

## Nginx Command Reference

| Command | Purpose |
|---|---|
| `sudo nginx -t` | Test configuration syntax |
| `sudo systemctl reload nginx` | Reload config without downtime |
| `sudo systemctl restart nginx` | Full restart (brief downtime) |
| `sudo systemctl status nginx` | Check service status |
| `sudo tail -f /var/log/nginx/digit-api.access.log` | Follow access log |
| `sudo tail -f /var/log/nginx/digit-api.error.log` | Follow error log |

---

*→ Next: [07 · Logging](../07-logging/logging.md)*
