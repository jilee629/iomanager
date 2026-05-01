# uv 설치
- ~/iomanager$ curl -LsSf https://astral.sh/uv/install.sh | sh
- ~/iomanager$ uv sync

# ufw 포트 허용
- ~/iomanager$ sudo iptables -I INPUT 6 -p tcp --dport 80 -j ACCEPT
- ~/iomanager$ sudo apt install iptables-persistent
- ~/iomanager$ sudo netfilter-persistent save

# gunicorn 
## gunicorn service 설정
```
~/iomanager$ cat /etc/systemd/system/gunicorn.service 
[Unit]
Description=gunicorn daemon
After=network.target

[Service]
User=ubuntu
Group=www-data
WorkingDirectory=/home/ubuntu/iomanager
ExecStart=/home/ubuntu/iomanager/.venv/bin/gunicorn \
        --workers 2 \
        --bind unix:/home/ubuntu/iomanager/gunicorn.sock \
        config.wsgi:application
UMask=007

[Install]
WantedBy=multi-user.target
```
## gunicon 확인
- ~/iomanager$ sudo systemctl daemon-reload
- ~/iomanager$ sudo systemctl start gunicorn
- ~/iomanager$ sudo systemctl enable gunicorn
- ~/iomanager$ uv run gunicorn --bind 0.0.0.0:8000 config.wsgi:application

# nginx
## nginx sites-available 설정
```
~/iomanager$ cat /etc/nginx/sites-available/iomanager 
server {
        listen 80;
        server_name 40.233.21.11;

        # listen 443 ssl;
        # 인증서 경로 설정
        # ssl_certificate /etc/ssl/certs/nginx-selfsigned.crt;
        # ssl_certificate_key /etc/ssl/private/nginx-selfsigned.key;
        # 보안을 위한 추가 설정 (선택 사항)
        # ssl_protocols TLSv1.2 TLSv1.3;
        # ssl_ciphers HIGH:!aNULL:!MD5;

        location = /favicon.ico { access_log off; log_not_found off; }

        location /static {
                alias /home/ubuntu/iomanager/staticfiles/;
        }

        location / {
                include proxy_params;
                proxy_pass http://unix:/home/ubuntu/iomanager/gunicorn.sock;
        }
}
~/iomanager$ sudo ln -s /etc/nginx/sites-available/iomanager /etc/nginx/sites-enabled/
```
## nginx 확인
- iomanager$ sudo nginx -t

# 정기권 만료 처리 crontab
```
5 0 * * * /home/ubuntu/iomanager/scripts/run_expire_passes.sh
```

## permission error
```
sudo tail -f /var/log/nginx/error.log
unix:/home/ubuntu/iomanager/gunicorn.sock failed (13: Permission denied) 
```
- ~/iomanager$ chmod 755 /home/ubuntu/iomanager
- ~/iomanager$ chmod 755 /home/ubuntu
