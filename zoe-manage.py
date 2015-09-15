#!/usr/bin/env python3

from argparse import ArgumentParser, Namespace
import logging

from zoe_scheduler.state import create_tables

argparser = None


def setup_db_cmd(_):
    create_tables()


def process_arguments() -> Namespace:
    global argparser
    argparser = ArgumentParser(description="Zoe - Container Analytics as a Service ops client")
    argparser.add_argument('-d', '--debug', action='store_true', default=False, help='Enable debug output')
    subparser = argparser.add_subparsers(title='subcommands', description='valid subcommands')

    argparser_setup_db = subparser.add_parser('setup-db', help="Create the tables in the database")
    argparser_setup_db.set_defaults(func=setup_db_cmd)

    return argparser.parse_args()


def main():
    args = process_arguments()
    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    try:
        args.func(args)
    except AttributeError:
        argparser.print_help()
        return

if __name__ == "__main__":
    main()
