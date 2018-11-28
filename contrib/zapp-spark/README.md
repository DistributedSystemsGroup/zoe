# Spark ZApp

URL: [https://gitlab.eurecom.fr/zoe-apps/zapp-spark](https://gitlab.eurecom.fr/zoe-apps/zapp-spark)

Combine the full power of a distributed [Apache Spark](http://spark.apache.org) cluster with Python Jupyter Notebooks.

The Spark shell can be used from the built-in terminal in the notebook ZApp.

Spark is configured in stand-alone, distributed mode. This ZApp contains Spark version 2.2.2.

## Changing the default configuration

When you start a kernel with this Zapp you will have a SparkContext already created for you with a default configuration.

You can modify the executor ram limit or add other options and re-create a new context by using the following code:

    # default options
    spark_executor_ram = int(os.environ["SPARK_WORKER_RAM"]) - (1024 ** 3) - (512 * 1024 ** 2)
    conf.set("spark.executor.memory", spark_executor_ram)
    
    # set other options as desired
    
    # create the context
    sc = pyspark.SparkContext(conf=conf)


## Customizing the ZApp

### Workers

To run your own script (for example to install additional libraries on the worker nodes) you can override the default command specified in the JSON file, in the service section corresponding to the workers.

To start the worker correctly, you will need to use this command-line at the end of your script:

    /opt/spark/bin/spark-class org.apache.spark.deploy.worker.Worker \
       spark://${SPARK_MASTER_IP}:7077 --cores ${SPARK_WORKER_CORES} --memory ${SPARK_WORKER_RAM} \
       -h ${SPARK_LOCAL_IP:-127.0.0.1}

### Master

To run your own script you can override the default command specified in the JSON file, in the service section corresponding to the master.

To start the master correctly, you will need to use this command-line at the end of your script:

    ${SPARK_HOME}/bin/spark-class org.apache.spark.deploy.master.Master --host ${SPARK_MASTER_IP} --port 7077 --webui-port 8080

### Notebook and Spark submit

You can customize the command run by the notebook service, to install additional libraries before starting the notebook, or to transform the ZApp into a batch job, by calling spark-submit instead of jupyter.

If you want to run the notebook, at the end of your script call `/opt/start_notebook.sh`.

If you want to run spark-submit, you need to use:

    /opt/spark/bin/spark-submit --master spark://${SPARK_MASTER_IP}:7077 <the rest of the options>

Where the rest of the options could be, for example:

    wordcount.py hdfs://192.168.45.157/datasets/gutenberg_big_2x.txt hdfs://192.168.45.157/tmp/wcount-out

