# Copyright (C) 2020 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
FROM clearlinux:latest

RUN swupd bundle-add nginx
RUN useradd nginx
COPY services/nginx/nginx.conf /etc/nginx/nginx.conf
COPY services/nginx/sites.conf /etc/nginx/conf.d/sites.conf
COPY services/nginx/*.pem /etc/nginx/ssl/
COPY telemetryui/telemetryui/static /var/www/static
RUN chown -R nginx:nginx /var/www/static

STOPSIGNAL SIGTERM

CMD ["nginx", "-g", "daemon off;"]
