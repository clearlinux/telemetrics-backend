import sys
import json
import psycopg2
import argparse


TIME_WINDOW = "30" # days
FLUSH_OLD_DATA =\
"""DELETE FROM records WHERE timestamp_client < (SELECT extract(EPOCH FROM now() - 
     interval '{} days')::Integer);""".format(TIME_WINDOW)

def parse_args():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True,
                    help="JSON file with values for DB")
    return ap.parse_args()


def load_configuration(conf_filename):
    with open(conf_filename, "r") as conf:
        conf_content = json.load(conf)
        return conf_content


def connect(conf):
    conn1 = psycopg2.connect(**conf)
    return conn1


def main(args):
    conf = load_configuration(args.config)
    src = connect(conf)
    cur = src.cursor()

    cur.execute(FLUSH_OLD_DATA)

    src.commit()
    cur.close()
    src.close()


if __name__ == '__main__':
    main(parse_args())
