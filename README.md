# uv 설치
- $ curl -LsSf https://astral.sh/uv/install.sh | sh
- ~/iomanager$ uv sync

# iptabes 허용
- $ sudo iptables -A INPUT -p tcp --dport 80 -j ACCEPT
- $ sudo iptables -L INPUT -vn
- $ sudo apt install iptables-persistent
- $ sudo netfilter-persistent save

# gunicorn 
## /etc/systemd/system/gunicorn.service
```
[Unit]
Description=gunicorn daemon
After=network.target

[Service]
User=ubuntu
Group=www-data
WorkingDirectory=/home/ubuntu/iomanager
ExecStart=/home/ubuntu/iomanager/.venv/bin/gunicorn \
        --workers 3 \
        --bind unix:/home/ubuntu/iomanager/gunicorn.sock \
        config.wsgi:application

[Install]
WantedBy=multi-user.target
```
- $ sudo systemctl daemon-reload
- $ sudo systemctl start gunicorn
- $ sudo systemctl enable gunicorn

## gunicon 테스트
- ~/iomanager$ uv run gunicorn --bind 0.0.0.0:8000 config.wsgi:application

# nginx
## /etc/nginx/sites-available/iomanager
```
server {
        listen 80;
        server_name 40.233.21.11;

        location = /favicon.ico { access_log off; log_not_found off; }

        location /static {
                alias /home/ubuntu/iomanager/staticfiles/;
        }

        location / {
                include proxy_params;
                proxy_pass http://unix:/home/ubuntu/iomanager/gunicorn.sock;
        }
}
```
- $ sudo ln -s /etc/nginx/sites-available/iomanager /etc/nginx/sites-enabled/


## nginx 테스트
- iomanager$ sudo nginx -t

## permission error
```
sudo tail -f /var/log/nginx/error.log
unix:/home/ubuntu/iomanager/gunicorn.sock failed (13: Permission denied) 
```
- $ chmod 755 /home/ubuntu/iomanager
- $ chmod 755 /home/ubuntu

# 정기권 만료 처리 crontab
```
5 0 * * * /home/ubuntu/iomanager/scripts/run_expire_passes.sh
```


