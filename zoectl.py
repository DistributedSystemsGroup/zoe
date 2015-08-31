from argparse import ArgumentParser, Namespace
import logging
from zipfile import is_zipfile

from zoe_client import ZoeClient
from common.state import create_tables


def status_cmd(_):
    client = ZoeClient()
    status_report = client.platform_status()
    print(status_report)


def setup_db_cmd(_):
    create_tables()


def user_new_cmd(args):
    client = ZoeClient()
    clid = client.user_new(args.email)
    print("New user ID: {}".format(clid))


def user_get_cmd(args):
    client = ZoeClient()
    clid = client.user_get(args.email)
    print("User ID: {}".format(clid))


def spark_cluster_new_cmd(args):
    client = ZoeClient()
    application = client.spark_application_new(args.user_id, args.worker_count, args.executor_memory, args.executor_cores, args.name)
    print("Spark application added with ID: {}".format(application.id))


def spark_notebook_new_cmd(args):
    client = ZoeClient()
    application = client.spark_notebook_application_new(args.user_id, args.worker_count, args.executor_memory, args.executor_cores, args.name)
    print("Spark application added with ID: {}".format(application.id))


def spark_submit_new_cmd(args):
    if not is_zipfile(args.file):
        print("Error: the file specified is not a zip archive")
        return
    client = ZoeClient()
    application = client.spark_submit_application_new(args.user_id, args.worker_count, args.executor_memory, args.executor_cores, args.name, args.file)
    print("Spark application added with ID: {}".format(application.id))


def run_spark_cmd(args):
    client = ZoeClient()
    application = client.spark_application_get(args.id)
    if application is None:
        print("Error: application {} does not exist".format(args.id))
        return
    ret = client.execution_spark_new(application, args.name, args.cmd, args.spark_opts)

    if ret:
        print("Application scheduled successfully, use the app-inspect command to check its status")
    else:
        print("Admission control refused to run the application specified")


def app_rm_cmd(args):
    client = ZoeClient()
    application = client.spark_application_get(args.id)
    if application is None:
        print("Error: application {} does not exist".format(args.id))
        return
    if args.force:
        a = client.application_status(application)
        for eid in a["executions"]:
            e = client.execution_get(eid)
            if e.status == "running":
                print("Terminating execution {}".format(e.name))
                client.execution_terminate(e)

    client.application_remove(application)


def app_inspect_cmd(args):
    client = ZoeClient()
    application = client.spark_application_get(args.id)
    if application is None:
        print("Error: application {} does not exist".format(args.id))
        return
    app_report = client.application_status(application)
    print(app_report)


def app_list_cmd(args):
    client = ZoeClient()
    applications = client.spark_application_list(args.id)
    if len(applications) > 0:
        print("{:4} {:20} {:25}".format("ID", "Name", "Type"))
    for app in applications:
        print("{:4} {:20} {:25}".format(app.id, app.name, app.type))


def exec_kill_cmd(args):
    client = ZoeClient()
    execution = client.execution_get(args.id)
    if execution is None:
        print("Error: execution {} does not exist".format(args.id))
        return
    client.execution_terminate(execution)


def log_get_cmd(args):
    client = ZoeClient()
    log = client.log_get(args.id)
    if log is None:
        print("Error: No log found for container ID {}".format(args.id))
    print(log)


def process_arguments() -> Namespace:
    argparser = ArgumentParser(description="Zoe - Container Analytics as a Service command-line client")
    argparser.add_argument('-d', '--debug', action='store_true', default=False, help='Enable debug output')
    subparser = argparser.add_subparsers(title='subcommands', description='valid subcommands')

    argparser_status = subparser.add_parser('status', help="Show the platform status")
    argparser_status.set_defaults(func=status_cmd)

    argparser_user_new = subparser.add_parser('user-new', help="Create a new user")
    argparser_user_new.add_argument('email', help="User email address")
    argparser_user_new.set_defaults(func=user_new_cmd)

    argparser_user_get = subparser.add_parser('user-get', help="Get the user id for an existing user")
    argparser_user_get.add_argument('email', help="User email address")
    argparser_user_get.set_defaults(func=user_get_cmd)

    argparser_setup_db = subparser.add_parser('setup-db', help="Create the tables in the database")
    argparser_setup_db.set_defaults(func=setup_db_cmd)

    argparser_spark_cluster_create = subparser.add_parser('app-spark-cluster-new', help="Setup a new empty Spark cluster")
    argparser_spark_cluster_create.add_argument('--user-id', type=int, required=True, help='Application owner')
    argparser_spark_cluster_create.add_argument('--name', required=True, help='Application name')
    argparser_spark_cluster_create.add_argument('--worker-count', type=int, default=2, help='Number of workers')
    argparser_spark_cluster_create.add_argument('--executor-memory', default='2g', help='Maximum memory available per-worker, the system assumes only one executor per worker')
    argparser_spark_cluster_create.add_argument('--executor-cores', default='2', type=int, help='Number of cores to assign to each executor')
    argparser_spark_cluster_create.set_defaults(func=spark_cluster_new_cmd)

    argparser_spark_nb_create = subparser.add_parser('app-spark-notebook-new', help="Setup a new Spark Notebook application")
    argparser_spark_nb_create.add_argument('--user-id', type=int, required=True, help='Notebook owner')
    argparser_spark_nb_create.add_argument('--name', required=True, help='Notebook name')
    argparser_spark_nb_create.add_argument('--worker-count', type=int, default=2, help='Number of workers')
    argparser_spark_nb_create.add_argument('--executor-memory', default='2g', help='Maximum memory available per-worker, the system assumes only one executor per worker')
    argparser_spark_nb_create.add_argument('--executor-cores', default='2', type=int, help='Number of cores to assign to each executor')
    argparser_spark_nb_create.set_defaults(func=spark_notebook_new_cmd)

    argparser_spark_submit_create = subparser.add_parser('app-spark-new', help="Setup a new Spark submit application")
    argparser_spark_submit_create.add_argument('--user-id', type=int, required=True, help='Application owner')
    argparser_spark_submit_create.add_argument('--name', required=True, help='Application name')
    argparser_spark_submit_create.add_argument('--worker-count', type=int, default=2, help='Number of workers')
    argparser_spark_submit_create.add_argument('--executor-memory', default='2g', help='Maximum memory available per-worker, the system assumes only one executor per worker')
    argparser_spark_submit_create.add_argument('--executor-cores', default='2', type=int, help='Number of cores to assign to each executor')
    argparser_spark_submit_create.add_argument('--file', required=True, help='zip archive containing the application files')
    argparser_spark_submit_create.set_defaults(func=spark_submit_new_cmd)

    argparser_app_rm = subparser.add_parser('app-rm', help="Delete an application")
    argparser_app_rm.add_argument('id', type=int, help="Application id")
    argparser_app_rm.add_argument('-f', '--force', action="store_true", help="Kill also all active executions, if any")
    argparser_app_rm.set_defaults(func=app_rm_cmd)

    argparser_app_inspect = subparser.add_parser('app-inspect', help="Gather details about an application and its active executions")
    argparser_app_inspect.add_argument('id', type=int, help="Application id")
    argparser_app_inspect.set_defaults(func=app_inspect_cmd)

    argparser_app_inspect = subparser.add_parser('app-ls', help="List all applications for a user")
    argparser_app_inspect.add_argument('id', type=int, help="User id")
    argparser_app_inspect.set_defaults(func=app_list_cmd)

    argparser_spark_app_run = subparser.add_parser('run', help="Execute a previously registered Spark application")
    argparser_spark_app_run.add_argument('id', type=int, help="Application id")
    argparser_spark_app_run.add_argument('--name', required=True, help='Execution name')
    argparser_spark_app_run.add_argument('--cmd', help="Command-line to pass to spark-submit")
    argparser_spark_app_run.add_argument('--spark-opts', help="Optional Spark options to pass to spark-submit")
    argparser_spark_app_run.set_defaults(func=run_spark_cmd)

    argparser_execution_kill = subparser.add_parser('execution-kill', help="Terminates an execution")
    argparser_execution_kill.add_argument('id', type=int, help="Execution id")
    argparser_execution_kill.set_defaults(func=exec_kill_cmd)

    argparser_log_get = subparser.add_parser('log-get', help="Retrieves the logs of a running container")
    argparser_log_get.add_argument('id', type=int, help="Container id")
    argparser_log_get.set_defaults(func=log_get_cmd)

    return argparser.parse_args()


def main():
    args = process_arguments()
    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    args.func(args)


main()
