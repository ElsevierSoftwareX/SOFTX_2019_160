# Installation

This library requires a copy of Python 3.5 in order  to function, as well as installation of the dependencies listed 
in the ```requirements.txt``` file. Steps are outlined below for installation as well as optional steps to make the
user experience better.

#### Required Steps

1. Python with managed environments
2. Installation of this package
3. Project dependencies
4. Creation of a ```local_config.py``` file

#### Optional Steps

1. Jupyter
2. IPython Kernel Customization
3. Setting up data, analysis notebooks, and datasets


## Installing Python through Conda

1. Install `conda` through the directions listed at [Anaconda](https://www.anaconda.com/download/), you want the Python 
3 version.
2. Create a Python 3.5 environment using the command ``conda create -n {name_of_your_env} python=3.5 scipy jupyter``. 
You can find more details in the conda docs at the 
[Conda User Guide](https://conda.io/docs/user-guide/tasks/manage-environments.html).
3. In order to use your new environment, you can use the scripts `source activate {name_of_your_env}` 
and `source deactivate`. Do this in any session where you will run your analysis or Jupyter.  

## Installation of this Package

Clone this repository somewhere convenient.

## Project Dependencies

Inside the cloned repository, after activating your environment, install dependencies:

1. Install `xrft` via `conda install -c conda-forge xrft`
2. Run `pip install -r requirements.txt`. This will
install all packages required by the code. If you ever want to add a new package you find elsewhere, just 
`pip install {package_name}` and add it to `requirements.txt`.

Alternatively, if you have a bash client run `install.sh` which will perform these two steps for you. 
Verify there are no errors on this step.  

## `local_config.py`

You need to tell the analysis code where your data and datasets are. To do this you need to make a 
Python file called `local_config.py` and put it into the `arpes` folder. Inside this file you 
should define the two variables `DATA_PATH` and `DATASET_CACHE_PATH`. These tell the project
where to look for data, and where to put cached computations, respectively. For reference, 
Conrad's looks like:

```
DATA_PATH = '/Users/chstansbury/Research/lanzara/data/'
DATASET_CACHE_PATH = '/Users/chstansbury/Research/lanzara/data/cache/'
```

## Environment

You need to make sure to export a variable ``ARPES_ROOT`` in order to run scripts. If you are on a UNIX-like system
you can add the following to your ``.bashrc``, ``.bash_profile`` or equivalent:

```bash
export ARPES_ROOT="/path/to/wherever/you/installed/this/project/"
```

The value of ``ARPES_ROOT`` should be defined so that ``$ARPES_ROOT/README.md`` points to the file that you 
are currently reading.

To make using the code simpler, consider an alias to move to the data analysis location and to start the 
virtual environment. On Conrad's computer this looks like:

```bash
alias arpes="cd $ARPES_ROOT && source activate python_arpes"
alias arpesn="cd $ARPES_ROOT && source activate python_arpes && jupyter notebook"
```

## Jupyter

You should already have Jupyter if you created an environment with `conda` according to the above. Ask Conrad
about good initial settings.

## IPython Kernel Customization

If you don't want to have to import everything all the time, you should customize your IPython session so that it
runs imports when you first spin up a kernel. There are good directions for how to do this online, but a short 
version is:

1. Create an IPython profile, use this to start your notebooks
2. In ``~/.ipython/{Your profile}/`` make a folder `startup`
3. Add the files ``~/.ipython/{Your profile}/startup/00-add-arpes-path.py`` and 
``~/.ipython/{Your profile}/startup/01-common-imports.ipy`` according to the templates in `ipython_templates`
4. Customize to your liking

Note that you can customize the default profile if you wish instead.

It is important that the filenames you put are such that ``-add-arpes-path`` is lexographically first, as this ensures
that it is executed first. The ``.ipy`` extension on ``01-common-imports.ipy`` is also essential.
Ask Conrad if any of this is confusing.

# Getting Started with Analysis

Ask Conrad! He will put some tutorial/example notebooks he has collected eventually.