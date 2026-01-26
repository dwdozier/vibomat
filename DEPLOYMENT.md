# Deployment Guide

This document provides guidance for deploying Vibomat to production environments.

## Proxy Configuration

### ProxyHeadersMiddleware Security

Vibomat uses FastAPI's `ProxyHeadersMiddleware` to handle proxy headers from reverse proxies
like Nginx or Caddy. For security, the application only trusts proxy headers
(`X-Forwarded-For`, `X-Real-IP`, etc.) from explicitly configured IP addresses.

#### Configuration

The `TRUSTED_PROXY_IPS` environment variable controls which proxy IPs are trusted:

```bash
# Default: localhost only (development)
TRUSTED_PROXY_IPS=127.0.0.1,::1

# Production: Add your reverse proxy's internal IP
TRUSTED_PROXY_IPS=127.0.0.1,::1,10.0.1.10

# Multiple proxies
TRUSTED_PROXY_IPS=127.0.0.1,::1,10.0.1.10,10.0.1.11
```

**Security Warning**: Never use `TRUSTED_PROXY_IPS=*` in production. This allows any client to
spoof their IP address and bypass rate limiting or IP-based access controls.

### Common Deployment Scenarios

#### 1. Docker Compose with Nginx

If you're using Docker Compose with an Nginx reverse proxy:

```yaml
# docker-compose.yml
services:
  backend:
    environment:
      # Trust the nginx container's IP
      TRUSTED_PROXY_IPS: "127.0.0.1,::1,172.18.0.2"
```

Find your nginx container's IP:

```bash
docker inspect nginx_container_name | grep IPAddress
```

#### 2. Kubernetes with Ingress

For Kubernetes deployments with an ingress controller:

```yaml
# deployment.yaml
env:
  - name: TRUSTED_PROXY_IPS
    # Trust the ingress controller's service CIDR
    value: "127.0.0.1,::1,10.96.0.0/16"
```

Note: CIDR notation is supported for IP ranges.

#### 3. Cloud Load Balancers

##### AWS ALB/NLB

```bash
# Trust AWS internal load balancer IPs
TRUSTED_PROXY_IPS=127.0.0.1,::1,10.0.0.0/8
```

##### Google Cloud Load Balancer

```bash
# Trust GCP load balancer health check and forwarding IPs
TRUSTED_PROXY_IPS=127.0.0.1,::1,35.191.0.0/16,130.211.0.0/22
```

##### Azure Application Gateway

```bash
# Trust Azure Application Gateway subnet
TRUSTED_PROXY_IPS=127.0.0.1,::1,10.1.0.0/24
```

#### 4. Cloudflare

When using Cloudflare as a reverse proxy, trust Cloudflare's IP ranges:

```bash
# Get latest Cloudflare IPs from https://www.cloudflare.com/ips/
TRUSTED_PROXY_IPS=127.0.0.1,::1,173.245.48.0/20,103.21.244.0/22,103.22.200.0/22
```

**Note**: Cloudflare IPs change periodically. Consider fetching them dynamically or subscribing
to their IP list updates.

### Nginx Configuration

When using Nginx as a reverse proxy, ensure it sets the forwarded headers:

```nginx
location / {
    proxy_pass http://backend:8000;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}
```

### Verification

To verify proxy headers are working correctly:

1. Check the application logs for the correct client IP
2. Test with rate limiting endpoints to ensure IP-based limits work
3. Use a tool like `curl` to verify headers:

```bash
# From behind the proxy
curl -H "X-Forwarded-For: 1.2.3.4" https://your-app.com/health

# Should log the actual client IP, not the spoofed one
```

### Troubleshooting

#### Issue: Real client IPs not showing in logs

**Solution**: Verify `TRUSTED_PROXY_IPS` includes your proxy's IP:

```bash
# Check current setting
docker exec backend printenv TRUSTED_PROXY_IPS

# Update docker-compose.yml or .env file
TRUSTED_PROXY_IPS=127.0.0.1,::1,<your_proxy_ip>
```

#### Issue: Rate limiting not working correctly

**Cause**: If proxy IPs are not trusted, all requests appear to come from the proxy IP.

**Solution**: Ensure `TRUSTED_PROXY_IPS` is correctly configured and Nginx is setting
`X-Forwarded-For`.

#### Issue: "Too many values to unpack" error

**Cause**: Incorrectly formatted `TRUSTED_PROXY_IPS` environment variable.

**Solution**: Use comma-separated values without spaces:

```bash
# Correct
TRUSTED_PROXY_IPS=127.0.0.1,::1,10.0.0.1

# Incorrect
TRUSTED_PROXY_IPS="127.0.0.1, ::1, 10.0.0.1"  # spaces cause issues
```

## Additional Security Considerations

### HTTPS/TLS

Always use HTTPS in production. Configure your reverse proxy to terminate TLS:

```nginx
server {
    listen 443 ssl http2;
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    # Modern TLS configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
}
```

### Rate Limiting

The application includes rate limiting middleware. Ensure your proxy configuration passes the
real client IP for rate limits to work correctly.

### CORS

Configure `BACKEND_CORS_ORIGINS` to include only your frontend domains:

```bash
BACKEND_CORS_ORIGINS=https://app.vibomat.com,https://www.vibomat.com
```

### Database

Use connection pooling and ensure database credentials are secured:

```bash
DATABASE_URL=postgresql+asyncpg://user:password@db:5432/vibomat
```

Store sensitive credentials in a secrets manager (AWS Secrets Manager, Google Secret Manager,
HashiCorp Vault, etc.).

## Monitoring

### Health Check

The application provides a health check endpoint:

```bash
curl https://your-app.com/health
# Response: {"status": "ok"}
```

Configure your load balancer to use this endpoint for health checks.

### Logging

Application logs are JSON-formatted for easy parsing. Configure log aggregation
(CloudWatch, Stackdriver, ELK stack) to collect logs from all instances.

### Metrics

Consider adding Prometheus metrics for monitoring:

- Request rate
- Response times
- Error rates
- Token refresh failures
- Database connection pool usage

## Backup and Recovery

### Database Backups

Set up automated database backups:

```bash
# PostgreSQL backup
pg_dump -U user vibomat > backup.sql

# Restore
psql -U user vibomat < backup.sql
```

### Redis Persistence

Configure Redis persistence for background task queues:

```redis
# redis.conf
save 900 1
save 300 10
save 60 10000
```

## Scaling

### Horizontal Scaling

The application is designed to scale horizontally:

1. Run multiple backend instances behind a load balancer
2. Use shared Redis for distributed locking and task queues
3. Use PostgreSQL with connection pooling

### Background Workers

Scale TaskIQ workers independently:

```bash
# Run multiple workers
docker-compose up --scale worker=3
```

## Environment Variables Reference

See `.env.example` for a complete list of environment variables. Key production settings:

- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string
- `SECRET_KEY`: Application secret key (generate with `openssl rand -hex 32`)
- `TRUSTED_PROXY_IPS`: Trusted proxy IP addresses
- `BACKEND_CORS_ORIGINS`: Allowed CORS origins
- `SPOTIFY_CLIENT_ID`, `SPOTIFY_CLIENT_SECRET`: Spotify API credentials
- `GEMINI_API_KEY`: Google Gemini API key

## Support

For deployment issues, please file an issue on GitHub or contact the development team.
