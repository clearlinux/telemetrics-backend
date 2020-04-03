FROM clearlinux:latest

WORKDIR /var/www/collector

RUN swupd bundle-add python3-basic uwsgi
RUN mkdir -p /var/www/collector/log /var/www/collector/socket
COPY ./deployments/services/collector/requirements.txt .
COPY ./deployments/services/collector/collector.ini .
COPY ./collector/collector /var/www/collector/collector
COPY ./utils/shared_utils/model.py /var/www/collector/collector/
RUN pip3 install -r requirements.txt
RUN groupadd -r webapp && useradd -r -g webapp webapp
RUN chown -R webapp:webapp /var/www/collector

USER webapp

CMD ["uwsgi", "--ini", "/var/www/collector/collector.ini"]
