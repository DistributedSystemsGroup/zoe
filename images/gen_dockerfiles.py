#!/usr/bin/python

import sys
import shutil

from jinja2 import Environment, FileSystemLoader

def copyfile(fname, dest):
	shutil.copy("files/" + fname, dest + "/files/" + fname)

if len(sys.argv) < 3:
	print("Usage: {} <spark version> <hadoop version>".format(sys.argv[0]))
	sys.exit(1)

ji_env = Environment(loader=FileSystemLoader('templates'))

common_tmpl = ji_env.get_template('common.tmpl')
common = common_tmpl.render(spark_version=sys.argv[1], hadoop_version=sys.argv[2])

# Master
master_tmpl = ji_env.get_template('master.tmpl')
master = common + "\n" + master_tmpl.render()
open("master/Dockerfile", "w").write(master)
for f in ["remove_alias.sh", "start-master.sh"]:
	copyfile(f, "master")

# Worker
worker_tmpl = ji_env.get_template('worker.tmpl')
worker = common + "\n" + worker_tmpl.render()
open("worker/Dockerfile", "w").write(worker)
for f in ["remove_alias.sh", "start-worker.sh"]:
	copyfile(f, "worker")

# Shell
shell_tmpl = ji_env.get_template('shell.tmpl')
shell = common + "\n" + shell_tmpl.render()
open("shell/Dockerfile", "w").write(shell)
for f in ["remove_alias.sh", "start-shell.sh"]:
	copyfile(f, "shell")

# Submit
submit_tmpl = ji_env.get_template('submit.tmpl')
submit = common + "\n" + submit_tmpl.render()
open("submit/Dockerfile", "w").write(submit)
for f in ["remove_alias.sh", "submit.sh"]:
	copyfile(f, "submit")

# Notebook
#nb_tmpl = ji_env.get_template('notebook.tmpl')
#nb = nb_tmpl.render()
#open("notebook/Dockerfile", "w").write(nb)

