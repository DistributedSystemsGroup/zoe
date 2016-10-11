#!/usr/bin/env bash

set -e

SSH_PROXY_IP=192.168.46.36
SSH_PROXY_PORT=32769

function print_help {
    echo "Usage: $0 <-z zapp file> <-d input directory> <-n execution name> [-u zoe username] [-D output directory] <commandline to execute>"
    echo
    echo "Will submit a batch ZApp for execution."
    echo "First it will copy (with rsync) all files recursively in the <input directory> to the Zoe workspace."
    echo "Then it will submit the ZApp for execution in Zoe with the specified <command> in the monitor service"
    echo "Then it will stream the log output from the monitor service to the console"
    echo "When the execution finishes, if -D has been specified, rsync the specified <output directory> locally"
    echo
    echo "You will need also to define the following environment options:"
    echo " - ZOE_USER: your username in Zoe"
    echo " - ZOE_PASSWORD: your password for Zoe"
    echo " - ZOE_URL: the Zoe URL endpoint"
    exit
}

while getopts ":hz:d:n:u:D:" opt; do
    case ${opt} in
        \?|h)
          print_help
          ;;
        u)
          USER=$OPTARG
          ;;
        n)
          EXEC_NAME=$OPTARG
          ;;
        z)
          ZAPP_FILE="$OPTARG"
          ;;
        d)
          INPUT_DIR="$OPTARG"
          ;;
         D)
          OUTPUT_DIR="$OPTARG"
          ;;
    esac
done
shift $((OPTIND-1))

ZAPP_COMMANDLINE="$@"

if [ -z "${ZOE_USER}" ]; then
    echo "No ZOE_USER environment variable defined"
    echo
    print_help
    exit 1
fi

if [ -z "${ZOE_PASS}" ]; then
    echo "No ZOE_PASS environment variable defined"
    read -s -p "Zoe password:" ZOE_PASS
    export ZOE_PASS
fi

if [ -z "${ZOE_URL}" ]; then
    echo "No ZOE_URL environment variable defined"
    echo
    print_help
    exit 1
fi

if [ -z "$ZAPP_FILE" ]; then
    echo "A ZApp description must be specified with the -z option"
    echo
    print_help
    exit 1
fi

if [ ! -f "$ZAPP_FILE" ]; then
    echo "The specified ZApp file does not exist"
    echo
    print_help
    exit 1
fi

if [ -z "$INPUT_DIR" ]; then
    echo "An input directory must be specified with the -d option"
    echo
    print_help
    exit 1
fi

if [ ! -d "$INPUT_DIR" ]; then
    echo "The specified input directory does not exist"
    echo
    print_help
    exit 1
fi

if [ -z "$EXEC_NAME" ]; then
    echo "The execution name (-n) parameter is required"
    echo
    print_help
    exit 1
fi

echo "Copying the input directory to the workspace"
rsync -e "ssh -p $SSH_PROXY_PORT" -az --info=progress2 --delete ${INPUT_DIR}/ ${ZOE_USER}@${SSH_PROXY_IP}:`basename ${INPUT_DIR}`
echo

tempname=`tempfile`

if [ -n "$ZAPP_COMMANDLINE" ]; then
    echo "Creating a temporary copy of the ZApp with the new command-line: $ZAPP_COMMANDLINE"
    cat "$ZAPP_FILE" | python scripts/zapp_set_command.py "$ZAPP_COMMANDLINE" > ${tempname}
    ZAPP_FILE=${tempname}
fi

./zoe.py start -s ${EXEC_NAME} ${ZAPP_FILE}
if [ $? -ne 0 ]; then
    exit
fi

echo
if [ -n "$OUTPUT_DIR" ]; then
    if [ -d "$OUTPUT_DIR" ]; then
        echo "WARNING: directory $OUTPUT_DIR already exists, its contents will be overwritten"
        echo "Press CTRL-C to exit or ENTER to continue"
        read key
    fi
    mkdir -p "$OUTPUT_DIR"
    echo "Copying the output directory from the workspace"
    rsync -e "ssh -p $SSH_PROXY_PORT" -az --info=progress2 --delete "${USER}@${SSH_PROXY_IP}:`basename ${INPUT_DIR}`"/ "${OUTPUT_DIR}"
    echo
fi
rm -f ${tempname}
echo "All done."
