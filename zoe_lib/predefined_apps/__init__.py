from .copier import copier_app
from .eurecom_aml_lab import spark_jupyter_notebook_lab_app
from .hadoop import hdfs_app
from .jupyter_spark import spark_jupyter_notebook_app
from .openmpi import openmpi_app
from .spark import spark_submit_app
from .test_sleep import sleeper_app

PREDEFINED_APPS = [
    copier_app,
    spark_jupyter_notebook_app,
    spark_jupyter_notebook_lab_app,
    hdfs_app,
    openmpi_app,
    spark_submit_app,
    sleeper_app
]
