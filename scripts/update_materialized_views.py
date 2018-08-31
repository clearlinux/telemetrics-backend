import sys
import json
import psycopg2
import argparse


MATERIALIZED_VIEWS = (
'processed.classifications',
'processed.builds',
'processed.os_map',)

REFRESH_QUERY = "REFRESH MATERIALIZED VIEW {}"

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

    for view in MATERIALIZED_VIEWS:
        print("Refreshing view {}".format(view))
        cur.execute(REFRESH_QUERY.format(view))

    src.commit()
    cur.close()
    src.close()


if __name__ == '__main__':
    main(parse_args())
