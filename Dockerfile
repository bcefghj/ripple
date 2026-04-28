# Ripple 2.0 多阶段 Dockerfile
# 部署:docker run -p 8000:8000 -p 80:80 -v ~/.ripple:/root/.ripple ripple:latest

FROM python:3.12-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    nginx git curl && rm -rf /var/lib/apt/lists/*

WORKDIR /opt/ripple

# Install dependencies
COPY apps/api/requirements.txt apps/api/requirements.txt
RUN pip install --no-cache-dir -r apps/api/requirements.txt

# Copy code
COPY apps/api/ apps/api/
COPY apps/web/ apps/web/
COPY apps/web-chat/ apps/web-chat/
COPY apps/streamlit_demo/ apps/streamlit_demo/
COPY deploy/ deploy/

# Nginx config
RUN cp deploy/nginx_ripple.conf /etc/nginx/sites-available/ripple && \
    ln -sf /etc/nginx/sites-available/ripple /etc/nginx/sites-enabled/ripple && \
    rm -f /etc/nginx/sites-enabled/default

# Init persistence dir
RUN mkdir -p /root/.ripple && chmod 700 /root/.ripple

EXPOSE 80 8000

# Entrypoint script
COPY <<'EOF' /opt/ripple/entrypoint.sh
#!/bin/bash
set -e
nginx
cd /opt/ripple/apps/api
exec uvicorn main:app --host 0.0.0.0 --port 8000 --workers 2
EOF
RUN chmod +x /opt/ripple/entrypoint.sh

CMD ["/opt/ripple/entrypoint.sh"]
