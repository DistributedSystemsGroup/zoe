from argparse import ArgumentParser, Namespace
import logging

from caaas_client import CAaaSClient
from common.state import create_tables


def status_cmd(_):
    client = CAaaSClient()
    status_report = client.platform_status()
    print(status_report)


def setup_db_cmd(_):
    create_tables()


def user_new_cmd(args):
    client = CAaaSClient()
    clid = client.user_new(args.email)
    print("New user ID: {}".format(clid))


def user_get_cmd(args):
    client = CAaaSClient()
    clid = client.user_get(args.email)
    print("User ID: {}".format(clid))


def spark_app_new_cmd(args):
    client = CAaaSClient()
    application = client.spark_application_new(args.user_id, args.worker_count, args.executor_memory, args.executor_cores)
    client.schedule_application(application)


def process_arguments() -> Namespace:
    argparser = ArgumentParser(description="CAaaS - Container Analytics as a Service command-line client")
    argparser.add_argument('-d', '--debug', action='store_true', default=False, help='Enable debug output')
    subparser = argparser.add_subparsers(title='subcommands', description='valid subcommands')

    argparser_status = subparser.add_parser('status', help="Show the platform status")
    argparser_status.set_defaults(func=status_cmd)

    argparser_user_new = subparser.add_parser('user-new', help="Create a new user")
    argparser_user_new.add_argument('--email', required=True, help="User email address")
    argparser_user_new.set_defaults(func=user_new_cmd)

    argparser_user_get = subparser.add_parser('user-get', help="Get the user id for an existing user")
    argparser_user_get.add_argument('--email', required=True, help="User email address")
    argparser_user_get.set_defaults(func=user_get_cmd)

    argparser_setup_db = subparser.add_parser('setup-db', help="Create the tables in the database")
    argparser_setup_db.set_defaults(func=setup_db_cmd)

    argparser_spark_cluster_create = subparser.add_parser('spark-app-new', help="Create an empty Spark cluster")
    argparser_spark_cluster_create.set_defaults(func=spark_app_new_cmd)
    argparser_spark_cluster_create.add_argument('--user-id', type=int, required=True, help='Application owner')
    argparser_spark_cluster_create.add_argument('--worker-count', type=int, default=2, help='Number of workers')
    argparser_spark_cluster_create.add_argument('--executor-memory', default='2g', help='Maximum memory available per-worker, the system assumes only one executor per worker')
    argparser_spark_cluster_create.add_argument('--executor-cores', default='2', help='Number of cores to assign to each executor')

    return argparser.parse_args()


def main():
    args = process_arguments()
    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    args.func(args)


main()
