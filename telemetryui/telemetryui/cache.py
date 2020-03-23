# Copyright (C) 2015-2020 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import ast
import redis
from . import app

REDIS_HOSTNAME = app.config.get('REDIS_HOSTNAME', 'localhost')
REDIS_PORT = app.config.get('REDIS_PORT', 6379)
REDIS_PASSWD = app.config.get('REDIS_PASSWD', None)


def get_cached_data(varname, expiration, funct, *args, **kwargs):
    try:
        redis_client = redis.StrictRedis(decode_responses=True,
                                         host=REDIS_HOSTNAME,
                                         port=REDIS_PORT,
                                         password=REDIS_PASSWD,);
        # Try to get data from redis first
        ret = redis_client.get(varname)
        if ret is not None:
            # Convert to original type if successful
            ret = ast.literal_eval(ret)
        else:
            # If nothing was found, query the database
            ret = funct(*args, **kwargs)
            # Convert to string representation and cache via redis
            redis_client.set(varname, repr(ret), ex=expiration)
    except redis.exceptions.ConnectionError as e:
        print("%s Redis probably isn't running?" % str(e))
        # If we can't connect to redis, just query directly
        ret = funct(*args, **kwargs)
    return ret 


def uncache_data(varname):
    try:
        redis_client = redis.StrictRedis(decode_responses=True);
        redis_client.delete(varname)
    except redis.exceptions.ConnectionError as e:
        print("%s Redis probably isn't running?" % str(e))
    return

# vi: ts=4 et sw=4 sts=4
