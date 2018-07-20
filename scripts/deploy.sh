#!/bin/bash
#
# Copyright 2017 Intel Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

REMOTE_APP_DIR="/var/www/telemetry"
DEBIAN_PKGS="build-essential python3 python3-dev python3-pip virtualenv libpq-dev nginx git uwsgi uwsgi-plugin-python3"
REDHAT_PKGS="gcc gcc-c++ make python34 python34-devel python34-pip python34-virtualenv postgresql-devel postgresql-server postgresql-contrib nginx git policycoreutils-python uwsgi uwsgi-plugin-python3"
CLR_BUNDLES="application-server database-basic database-basic-dev python-basic os-core-dev web-server-basic"
DB_PASSWORD=""
NGINX_USER=""
NGINX_GROUP=""
REPO_NAME="telemetrics-backend"
TELEMETRYUI_INI="telemetryui_uwsgi.ini"
SPOOL_DIR="uwsgi-spool"
APT_GET_INSTALL="DEBIAN_FRONTEND=noninteractive apt-get install -y -o Dpkg::=\"--force-confnew\""
APT_GET_REMOVE="DEBIAN_FRONTEND=noninteractive apt-get remove -y -o Dpkg::=\"--force-confnew\""
YUM_INSTALL="yum install -y"

usage() {
  echo "Usage: $0 -H DOMAIN [OPTIONS]"
  echo -en "\n"
  echo "Deploy snapshot of the telemetrics-backend"
  echo -en "\n"
  echo -e "  -a\tPerform specified action (deploy, install, migrate, resetdb, restart, uninstall; default: deploy)"
  echo -e "  -d\tDistro to deploy to (ubuntu, centos or clr; default: ubuntu)"
  echo -e "  -h\tPrint these options"
  echo -e "  -H\tSet domain for deployment (only accepted value is \"localhost\" for now)"
  echo -e "  -r\tSet repo location to deploy from (default: https://github.com/clearlinux/telemetrics-backend)"
  echo -e "  -s\tSet source location (default: \"master\" branch from git repo)"
  echo -e "  -t\tSet source type (tarball, or git; default: git)"
  echo -e "  -u\tPerform complete uninstallation"
  exit 2
}

try_func() {
  local t=$(type -t $1)
  if [ "$t" != "function" ]; then
    return
  else
    # call it
    $1
  fi
}

error() {
  echo "ERROR: $1" >&2
}

if [ $# -eq 0 ]; then
  error "Missing required -H option"
  echo -en "\n"
  usage
fi

ACTION=

while getopts "a:d:hH:r:s:t:u" arg; do
  case $arg in
    a)
      case $OPTARG in
        deploy|install|migrate|resetdb|restart|uninstall)
          ACTION="$OPTARG"
          ;;
        *)
          error "invalid argument for -a ($OPTARG)"
          echo -en "\n"
          usage
          ;;
      esac
      ;;
    d)
      case $OPTARG in
        ubuntu)
          DISTRO="$OPTARG"
          NGINX_USER="www-data"
          NGINX_GROUP="www-data"
          ;;
        clr)
          DISTRO="$OPTARG"
          NGINX_USER="httpd"
          NGINX_GROUP="httpd"
          ;;
        centos)
          DISTRO="$OPTARG"
          NGINX_USER="nginx"
          NGINX_GROUP="nginx"
          ;;
        *)
          error "invalid argument for -d ($OPTARG)"
          echo -en "\n"
          usage
          ;;
      esac
      ;;
    h)
      usage
      ;;
    H)
      HOSTNAME="$OPTARG"
      ;;
    r)
      REPO_LOCATION="$OPTARG"
      ;;
    s)
      SOURCE="$OPTARG"
      ;;
    t)
      case $OPTARG in
        tarball|git)
          TYPE="$OPTARG"
          ;;
        *)
          error "invalid argument for -t ($OPTARG)"
          echo -en "\n"
          usage
          ;;
      esac
      ;;
    u)
      UNINSTALL_ALL=1
      ;;
    *)
      # Bash will print errors for getopts issues
      echo -en "\n"
      usage
      ;;
  esac
done

if [ -z "$HOSTNAME" ]; then
  error "Missing required -H option"
  echo -en "\n"
  usage
fi

if [ -z "$ACTION" ]; then
  ACTION="deploy"
fi
if [ -z "$DISTRO" ]; then
  DISTRO="ubuntu"
  NGINX_USER="www-data"
  NGINX_GROUP="www-data"
fi
if [ -z "$REPO_LOCATION" ]; then
  REPO_LOCATION="https://github.com/clearlinux/$REPO_NAME"
fi
if [ -z "$SOURCE" ]; then
  SOURCE="master"
fi
if [ -z "$TYPE" ]; then
  TYPE="git"
fi

echo "Options:"
echo "  host: $HOSTNAME"
echo "  distro: $DISTRO"
echo "  action: $ACTION"
echo "  repo: $REPO_LOCATION"
echo "  source: $SOURCE"
echo "  type: $TYPE"

do_restart() {
  sudo systemctl daemon-reload
  sudo systemctl restart nginx
  sudo systemctl restart uwsgi
}

set_proxy() {
  if [ -z "$https_proxy" ]; then
    echo "Try setting the https_proxy environment variable if you run into problems."
  else
    export https_proxy
  fi
}

do_migrate() {
  set_proxy
  (
    cd $REMOTE_APP_DIR/telemetryui
    sudo bash -c "export https_proxy=$https_proxy; virtualenv -p /usr/bin/python3 ../venv"
    sudo bash -c "export https_proxy=$https_proxy; source ../venv/bin/activate && FLASK_APP=run.py flask db upgrade"
  )
}

_install_ubuntu_reqs() {
  set_proxy
  sudo https_proxy=$https_proxy apt-get update
  sudo https_proxy=$https_proxy $APT_GET_INSTALL $DEBIAN_PKGS
  sudo https_proxy=$https_proxy pip3 install uwsgitop
}

_install_clr_reqs() {
  set_proxy
  sudo https_proxy=$https_proxy swupd bundle-add $CLR_BUNDLES
  sudo https_proxy=$https_proxy pip3 install uwsgitop
}

_install_centos_reqs() {
  set_proxy
  sudo https_proxy=$https_proxy yum check-update
  sudo https_proxy=$https_proxy $YUM_INSTALL epel-release
  sudo https_proxy=$https_proxy $YUM_INSTALL $REDHAT_PKGS
  sudo https_proxy=$https_proxy pip3 install uwsgitop
  sudo ln /usr/bin/virtualenv-3 /usr/bin/virtualenv
}

_write_requirements() {
    cat > $1 << EOF
alembic==0.9.5
click==6.7
Flask==0.12.2
Flask-Migrate==2.1.0
Flask-SQLAlchemy==2.2
Flask-WTF==0.14.2
itsdangerous==0.24
Jinja2==2.9.6
Mako==1.0.7
MarkupSafe==1.0
psycopg2==2.7.3
python-dateutil==2.6.1
python-editor==1.0.3
six==1.10.0
SQLAlchemy==1.1.13
Werkzeug==0.12.2
WTForms==2.1
EOF
}

_install_pip_pkgs() {
  local log=$REMOTE_APP_DIR/install.log
  local reqs=$1
  sudo rm -f "$log"
  if [ $DISTRO == "clr" ]; then
    # the latest psycopg2 binary package is incompatible with the glibc 2.26 on Clear Linux
    sudo bash -c "https_proxy=$https_proxy source venv/bin/activate && https_proxy=$https_proxy pip3 --log $log install --no-binary psycopg2 -r $reqs"
  else
    sudo bash -c "https_proxy=$https_proxy source venv/bin/activate && https_proxy=$https_proxy pip3 --log $log install -r $reqs"
  fi
}

_install_virtual_env() {
  set_proxy

  sudo mkdir -pv $REMOTE_APP_DIR
  (
    cd $REMOTE_APP_DIR
    sudo bash -c "https_proxy=$https_proxy virtualenv -p /usr/bin/python3 venv"
    local REQS=requirements.txt
    if [ ! -f ${REQS} ]; then
       local REQS=$(mktemp /tmp/requirements.txt.XXXXXX)
       _write_requirements $REQS
    fi
    _install_pip_pkgs $REQS
    sudo chown -R $NGINX_USER:$NGINX_GROUP $REMOTE_APP_DIR
  )
  sudo mkdir -pv /var/log/uwsgi
  sudo chown -R $NGINX_USER:$NGINX_GROUP /var/log/uwsgi
}

_postinstall_postgres_clr() {
  # postgres user is a system account (locked, no login shell, etc), so we need to modify it to make it usable
  sudo usermod -d /var/lib/pgsql -s /bin/bash -U postgres
  echo "Enter password for 'postgres' user:"
  sudo passwd postgres

  # clr-specific service for installation
  sudo systemctl start postgresql-install.service

  # trust all local users/connections
  sudo sed -i 's/reject$/trust/' /var/lib/pgsql/data/pg_hba.conf

  # make sure psql history file can be written
  sudo chown postgres:postgres /var/lib/pgsql

  # less is more
  sudo sh -c 'echo "export PAGER=less" >> /var/lib/pgsql/.profile'
  sudo chown postgres:postgres /var/lib/pgsql/.profile
}

_postinstall_postgres_centos() {
  sudo postgresql-setup initdb
  sudo sed -i 's/ident$/md5/' /var/lib/pgsql/data/pg_hba.conf
}

_start_postgres() {
  sudo systemctl enable postgresql
  sudo systemctl restart postgresql
}

_install_postgres_ubuntu() {
  set_proxy

  sudo https_proxy=$https_proxy $APT_GET_INSTALL postgresql postgresql-contrib
  _start_postgres
}

_stage_from_tarball() {
  local tarball=$1
  cp -f $tarball /tmp/backend_local.tar.gz
}

_stage_from_git() {
  local branch=$1
  local path="/tmp"

  (
    cd $path
    rm -rf $REPO_NAME
    git clone -b $branch $REPO_LOCATION
    rm -f $REPO_NAME/telemetryui/telemetryui/config_local.py
    tar -czf backend_local.tar.gz $REPO_NAME
  )
}

_stage_from_path() {
  # Currently not supported
  return
}

_subst_config() {
  local source="$1"
  if [ -n "$2" ]; then
    local destdir="$2"
  fi

  local tmp=$(mktemp -p $PWD)
  cat > "$tmp" << EOF
s|@@install_path@@|$REMOTE_APP_DIR/|
s|@@db_password@@|$DB_PASSWORD|
s|@@nginx_user@@|$NGINX_USER|
s|@@nginx_group@@|$NGINX_GROUP|
s|@@flask_key@@|$FLASK_KEY|
s|@@uwsgi_bin_path@@|$UWSGI_PATH|
EOF

  sed -i.backup -f "$tmp" $source

  rm "$tmp"

  if [ -n "$destdir" ]; then
    cp -av $source $destdir/
  fi
}

_get_db_pass() {
  local pass

  if [ ! -f $conf ]; then
    error "missing config.py file; must run the 'install' action first"
    exit 1
  fi

  grep -q '@@db_password@@' $conf
  if [ $? -eq 0 ]; then
    error "missing db password; must run the 'install' action first"
    exit 1
  fi

  pass=$(sed -n -e 's|^.*SQLALCHEMY_DATABASE_URI.*postgres://postgres:\(.*\)@localhost/telemetry.*|\1|p' $conf)
  echo "$pass"
}

_config_nginx_ubuntu() {
  sudo rm -f /etc/nginx/sites-enabled/default
  sudo rm -f /etc/nginx/sites-enabled/sites_nginx.conf
  sudo ln -sf $REMOTE_APP_DIR/sites_nginx.conf /etc/nginx/sites-enabled/
}

_config_nginx_clr() {
  sudo mkdir -pv /etc/nginx/conf.d
  sudo cp -av /usr/share/nginx/conf/nginx.conf.example /etc/nginx/nginx.conf
  sudo ln -sf $REMOTE_APP_DIR/sites_nginx.conf /etc/nginx/conf.d/
  sudo systemctl enable nginx
}

_config_nginx_centos() {
  sudo mkdir -pv /etc/nginx/conf.d
  sudo cp -av $scripts_path/nginx.conf /etc/nginx/nginx.conf
  sudo ln -sf $REMOTE_APP_DIR/sites_nginx.conf /etc/nginx/conf.d/
  sudo chcon -t httpd_config_t $REMOTE_APP_DIR/sites_nginx.conf
  sudo systemctl enable nginx
}

_config_uwsgi_ubuntu() {
  sudo cp -af $scripts_path/uwsgi.conf /etc/init/
  sudo cp -af $scripts_path/uwsgi.service /lib/systemd/system/
}

_config_uwsgi_clr() {
  sudo mkdir -pv /etc/systemd/system
  sudo cp -afv $scripts_path/uwsgi.service /etc/systemd/system/
  sudo systemctl daemon-reload
}

_config_uwsgi_centos() {
  sudo mkdir -pv /etc/systemd/system
  sudo cp -afv $scripts_path/uwsgi.service /etc/systemd/system/
  sudo systemctl daemon-reload
  cd $REMOTE_APP_DIR
  sudo cp -afv $scripts_path/nginx-uwsgi.te .
  sudo checkmodule -M -m -o nginx-uwsgi.mod nginx-uwsgi.te
  sudo semodule_package -o nginx-uwsgi.pp -m nginx-uwsgi.mod
  sudo semodule -i nginx-uwsgi.pp
}

_generate_key() {
  echo $(head -c 32 /dev/urandom | base64 -)
}

_get_flask_key() {
  local key
  local conf=$REMOTE_APP_DIR/telemetryui/telemetryui/config.py

  # Generate a new key if an existing config is not installed
  if [ ! -f $conf ]; then
    key=$(_generate_key)
    echo "$key"
    return
  fi

  # Generate a new key if the existing config is incomplete
  grep -q '@@flask_key@@' $conf
  if [ $? -eq 0 ]; then
    key=$(_generate_key)
    echo "$key"
    return
  fi

  # Else, use the existing key from the config
  key=$(sed -n -e "s|^.*SECRET_KEY = '\(..*\)'|\1|p" $conf)
  echo "$key"
}

_deploy() {
  local repo="/tmp/$REPO_NAME"
  local telemetryui_path="$repo/telemetryui"
  local shared_path="$repo/shared"
  local scripts_path="$repo/scripts"

  if [ -z "$DB_PASSWORD" ]; then
    DB_PASSWORD=$(_get_db_pass)
    export DB_PASSWORD
  fi

  if [ -z "$FLASK_KEY" ]; then
    FLASK_KEY=$(_get_flask_key)
    export FLASK_KEY
  fi

  # FIXME: enable remote deployment capability
  rm -rf $repo
  mv /tmp/backend_local.tar.gz /tmp/backend.tar.gz
  tar -C /tmp/ -xf /tmp/backend.tar.gz

  # Finalize configuration for telemetryui
  _subst_config "$scripts_path/$TELEMETRYUI_INI" "$telemetryui_path/"
  _subst_config "$scripts_path/uwsgi.conf"
  _subst_config "$scripts_path/sites_nginx.conf"
  # get uwsgi location, in case this was installed during script exec
  UWSGI_PATH=$(type -p uwsgi)
  _subst_config "$scripts_path/uwsgi.service"

  # Finalize configuration for postgres
  _subst_config "$telemetryui_path/telemetryui/config.py"

  # Install telemetryui + spooldir
  sudo cp -af $telemetryui_path $REMOTE_APP_DIR/
  sudo mkdir -pv $REMOTE_APP_DIR/telemetryui/$SPOOL_DIR

  # Install modules that are shared between apps
  sudo cp -af $shared_path $REMOTE_APP_DIR/

  # Install nginx config
  sudo cp -af $scripts_path/sites_nginx.conf $REMOTE_APP_DIR/

  # Install uwsgi config
  _config_uwsgi_${DISTRO}

  # Fix up permissions
  sudo chown -R $NGINX_USER:$NGINX_GROUP $REMOTE_APP_DIR/telemetryui

  # Modify existing nginx config
  _config_nginx_${DISTRO}

  # Misc uwsgi config
  sudo mkdir -pv /etc/uwsgi/vassals
  sudo ln -sf $REMOTE_APP_DIR/telemetryui/telemetryui_uwsgi.ini /etc/uwsgi/vassals/
  sudo systemctl enable uwsgi

  # Cert configuration
  if [ ! -f /etc/nginx/ssl/telemetry.cert.pem ]; then
    sudo sed -i.backup 's/\(ssl_.*\)/# \1/;s/\(listen.*443 ssl\)/# \1/' $REMOTE_APP_DIR/sites_nginx.conf
  fi
}

_clean_up() {
  rm -rf /tmp/$REPO_NAME
  rm -f /tmp/backend.tar.gz
}

do_deploy() {
  _stage_from_$TYPE $SOURCE
  _deploy
  _clean_up
  do_restart
}

_set_db_pass() {
  local pass
  echo -n "DB password: (default: postgres): " >&2
  read -s pass
  echo -en "\n" >&2
  if [ -z "$pass" ]; then
    pass="postgres"
  fi
  echo $pass
}

_drop_db() {
  sudo -u postgres dropdb telemetry
}

_create_db() {
  local scripts_path="/tmp/$REPO_NAME/scripts"

  # First, detect if the database already exists. If so, nothing to do here.
  sudo -u postgres psql --list --pset format=unaligned | grep -q '^telemetry|'
  if [ $? -eq 0 ]; then
    return 0
  fi

  if [ -z "$DB_PASSWORD" ]; then
    DB_PASSWORD=$(_set_db_pass)
    export DB_PASSWORD
  fi

  sudo -u postgres createdb telemetry > /dev/null 2>&1
  if [ $? -eq 0 ]; then
    sudo -u postgres psql template1 -c "ALTER USER postgres with encrypted password '$DB_PASSWORD';"
  else
    error "failed to create telemetry Postgres database"
    _drop_db
    exit 1
  fi
}

_update_db_pass() {
  local src_telemetryui_path="/tmp/$REPO_NAME/telemetryui"
  local dest_telemetryui_path="$REMOTE_APP_DIR/telemetryui"

  if [ -z "$DB_PASSWORD" ]; then
    DB_PASSWORD=$(_set_db_pass)
    export DB_PASSWORD
  fi

  # Restore the template files from the backups first
  if [ -f $src_telemetryui_path/config.py.backup ]; then
    mv $src_telemetryui_path/config.py.backup $src_telemetryui_path/config.py
  fi
}

do_install() {
  DB_PASSWORD=$(_set_db_pass)

  _install_${DISTRO}_reqs
  _install_virtual_env

  if [ ! -f /usr/bin/createdb ]; then
    try_func _install_postgres_${DISTRO}
  fi

  pgrep postgresql > /dev/null 2>&1
  if [ $? -ne 0 ]; then
    try_func _postinstall_postgres_${DISTRO}
    _start_postgres
  fi

  _stage_from_$TYPE $SOURCE
  _deploy
  _create_db
  _update_db_pass

  do_migrate
  _clean_up
  do_restart

  echo ""
  echo "Install complete (installation folder: ${REMOTE_APP_DIR})"
  echo ""
}

do_resetdb() {
  if [ -z "$DB_PASSWORD" ]; then
    DB_PASSWORD=$(_set_db_pass)
    export DB_PASSWORD
  fi

  _drop_db
  _create_db
  _update_db_pass
  do_migrate
}

_uninstall_ubuntu_pkgs() {
  sudo $APT_GET_REMOVE postgresql postgresql-contrib
  sudo rm -rv $REMOTE_APP_DIR
  sudo rm -rfv /etc/init/uwsgi.conf
  sudo rm -rfv /lib/systemd/system/uwsgi.service
  sudo rm -rv /etc/uwsgi/vassals
  sudo bash -c "yes | pip3 uninstall uwsgitop"
  sudo $APT_GET_REMOVE $DEBIAN_PKGS
}

do_uninstall() {
  _drop_db
  sudo rm -fv /etc/nginx/sites-enabled/sites_nginx.conf
  sudo rm -fv /etc/nginx/sites-enabled/default
  sudo ln -s /etc/nginx/sites-available/default /etc/nginx/sites-enabled/

  if [ -n $UNINSTALL_ALL ]; then
    try_func _uninstall_${DISTRO}_pkgs
  fi
}

case $ACTION in
  deploy)
    do_deploy
    ;;
  install)
    do_install
    ;;
  migrate)
    do_migrate
    ;;
  resetdb)
    do_resetdb
    ;;
  restart)
    do_restart
    ;;
  uninstall)
    do_uninstall
    ;;
  *)
    ;;
esac


exit 0


# vi: ft=sh sw=2 et sts=2
