# Notebook for Data Science

This ZApp contains a Jupyter Notebook with a Python 3.5 kernel and the following libraries:

* Tensorflow 1.10.1, Tensorboard 1.10.0
* Pytorch and TorchVision 0.4.1
* pandas, matplotlib, scipy, seaborn, scikit-learn, scikit-image, sympy, cython, patsy, statsmodel, cloudpickle, dill, numba, bokeh

The GPU version contains also CUDA 9.0 and tensorflow with GPU support

## Customizations

### Adding Python libraries

To install additional libraries you can add the following code on top of your notebook:

    import subprocess
	import sys

	def install(package):
	    subprocess.call([sys.executable, "-m", "pip", "--user", "install", package])

and call the `install(<package name>)` function to install all packages you need.

Finally restart the kernel to load the modules you just installed.

### Running your own script

By modifying the `command` parameter in the JSON file you can tell Zoe to run your own script instead of the notebook.

In this ZApp the default command is:

    "command": "jupyter lab --no-browser --NotebookApp.token='' --allow-root --ip=0.0.0.0"

If you change the JSON and write:

    "command": "/mnt/workspace/myscript.sh"

Zoe will run myscript.sh instead of running the Jupyter notebook. In this way you can:

 * transform an interactive notebook ZApp into a batch one, with exactly the same libraries and environment
 * perform additional setup before starting the notebook. In this case you will have to add the jupyter lab command defined above at the end of your script.

