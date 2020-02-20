FROM clearlinux:latest

RUN swupd bundle-add nginx
RUN useradd nginx
COPY nginx.conf /etc/nginx/nginx.conf
COPY sites.conf /etc/nginx/conf.d/sites.conf
COPY *.pem /etc/nginx/ssl/

STOPSIGNAL SIGTERM

CMD ["nginx", "-g", "daemon off;"]
