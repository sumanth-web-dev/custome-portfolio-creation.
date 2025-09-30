# Portfolio App Deployment Guide

## Environment Variables Configuration

Create a `.env` file with the following configurations:

```env
# App Secret (generate a strong secret key)
SECRET_KEY=your-secret-key-here

# Domain Configuration
DOMAIN_URL=https://portfolio.example.com
ALLOWED_HOSTS=portfolio.example.com,www.portfolio.example.com

# SSL Configuration (if using HTTPS directly)
SSL_CERT_PATH=/path/to/cert.pem
SSL_KEY_PATH=/path/to/key.pem

# SMTP Configuration for Email
SMTP_SERVER=smtp.example.com
SMTP_PORT=587
SMTP_USERNAME=your-smtp-username
SMTP_PASSWORD=your-smtp-password
SMTP_FROM=no-reply@portfolio.example.com

# Flask Configuration
FLASK_ENV=production
FLASK_DEBUG=false
```

## Nginx Configuration Example

Here's a sample Nginx configuration for reverse proxy setup:

```nginx
server {
    listen 80;
    server_name portfolio.example.com www.portfolio.example.com;

    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl;
    server_name portfolio.example.com www.portfolio.example.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    # SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;

    # Proxy settings
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Static files
    location /static {
        alias /path/to/your/app/static;
        expires 30d;
        add_header Cache-Control "public, no-transform";
    }
}
```

## Deployment Steps

1. Set up your server:
   ```bash
   # Install dependencies
   sudo apt update
   sudo apt install python3-pip python3-venv nginx

   # Create a virtual environment
   python3 -m venv venv
   source venv/bin/activate

   # Install requirements
   pip install -r requirements.txt
   ```

2. Configure environment:
   - Copy the `.env.example` file to `.env`
   - Update all environment variables with your values
   - Make sure the SSL certificates are in place if using HTTPS

3. Set up Nginx:
   - Copy the Nginx configuration to `/etc/nginx/sites-available/portfolio`
   - Create a symbolic link: `sudo ln -s /etc/nginx/sites-available/portfolio /etc/nginx/sites-enabled/`
   - Test configuration: `sudo nginx -t`
   - Restart Nginx: `sudo systemctl restart nginx`

4. Run the application with Gunicorn:
   ```bash
   gunicorn -w 4 -b 127.0.0.1:8000 app:app
   ```

5. Set up systemd service (optional):
   Create `/etc/systemd/system/portfolio.service`:
   ```ini
   [Unit]
   Description=Portfolio App
   After=network.target

   [Service]
   User=www-data
   WorkingDirectory=/path/to/your/app
   Environment="PATH=/path/to/your/app/venv/bin"
   EnvironmentFile=/path/to/your/app/.env
   ExecStart=/path/to/your/app/venv/bin/gunicorn -w 4 -b 127.0.0.1:8000 app:app

   [Install]
   WantedBy=multi-user.target
   ```

   Then start the service:
   ```bash
   sudo systemctl start portfolio
   sudo systemctl enable portfolio
   ```

## Security Considerations

1. Always use HTTPS in production
2. Keep your secret key secure and never commit it to version control
3. Regularly update dependencies
4. Use strong passwords for admin accounts
5. Configure proper file permissions
6. Implement rate limiting for API endpoints
7. Regular backup of the database

## Monitoring

1. Set up logging:
   ```python
   import logging
   logging.basicConfig(
       filename='portfolio.log',
       level=logging.INFO,
       format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
   )
   ```

2. Monitor system resources:
   - Use tools like `htop`, `nginx-status`
   - Consider setting up Prometheus + Grafana

3. Set up alerts for:
   - High server load
   - Error rates
   - Failed login attempts
   - Disk space usage