#!/bin/bash
# SSL 인증서 초기 발급 스크립트
# EC2에서 최초 1회 실행: bash init-ssl.sh

set -e

DOMAIN="dayone01.site"
EMAIL="admin@dayone01.site"

echo "=== Step 1: Starting containers with HTTP only ==="
# nginx가 SSL 없이 시작할 수 있도록 임시 자체 서명 인증서 생성
mkdir -p ./certbot/conf/live/$DOMAIN
docker compose run --rm --entrypoint "\
  openssl req -x509 -nodes -newkey rsa:2048 -days 1 \
    -keyout /etc/letsencrypt/live/$DOMAIN/privkey.pem \
    -out /etc/letsencrypt/live/$DOMAIN/fullchain.pem \
    -subj '/CN=localhost'" certbot

echo "=== Step 2: Starting nginx ==="
docker compose up -d frontend

echo "=== Step 3: Requesting Let's Encrypt certificate ==="
# 임시 인증서 삭제 후 진짜 인증서 발급
docker compose run --rm --entrypoint "\
  rm -rf /etc/letsencrypt/live/$DOMAIN && \
  rm -rf /etc/letsencrypt/archive/$DOMAIN && \
  rm -rf /etc/letsencrypt/renewal/$DOMAIN.conf" certbot

docker compose run --rm --entrypoint "\
  certbot certonly --webroot -w /var/www/certbot \
    --email $EMAIL \
    -d $DOMAIN \
    --agree-tos \
    --no-eff-email \
    --force-renewal" certbot

echo "=== Step 4: Restarting all services ==="
docker compose down
docker compose up -d

echo "=== Done! HTTPS is now active for $DOMAIN ==="
