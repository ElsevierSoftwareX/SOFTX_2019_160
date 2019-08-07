# pylint: disable=unused-import

import warnings
import contextlib

from typing import Union

VERSION = '2.1.2'


def check() -> None:
    """
    Verifies certain aspects of the installation and provides guidance for semi-broken installations.
    :return:
    """

    def verify_qt_tool() -> Union[str, None]:
        pip_command = 'pip install pyqtgraph'
        warning = 'Using qt_tool, the PyARPES version of Image Tool, requires ' \
                  'pyqtgraph and Qt5:\n\n\tYou can install with: {}'.format(pip_command)
        try:
            import pyqtgraph
        except ImportError:
            return warning
        return None

    def verify_igor_pro() -> Union[str, None]:
        pip_command = 'pip install https://github.com/chstan/igorpy/tarball/712a4c4#egg=igor-0.3.1'
        warning = 'For Igor support, install igorpy with: {}'.format(pip_command)
        warning_incompatible = 'PyARPES requires a patched copy of igorpy, ' \
                               'available at \n\thttps://github.com/chstan/igorpy/tarball/712a4c4\n\n\tYou can install with: ' \
                               '{}'.format(pip_command)
        try:
            import igor
            if igor.__version__ <= '0.3':
                raise ValueError('Not using patched version of igorpy.')

        except ImportError:
            return warning
        except ValueError:
            return warning_incompatible
        return None

    def verify_bokeh() -> Union[str, None]:
        pip_command = 'pip install bokeh==0.12.10'

        warning = 'For bokeh support, install version 0.12.10\n\t with {}'.format(pip_command)
        warning_incompatible = 'PyARPES, requires version 0.12.10 of bokeh. You can install with \n\t{}'.format(pip_command)

        try:
            import bokeh
            if not bokeh.__version__ == '0.12.10':
                raise ValueError('Not using the specified version of Bokeh.')

        except ImportError:
            return warning
        except ValueError:
            return warning_incompatible
        return None

    def verify_everything() -> Union[str, None]:
        import os
        phony_datasets = os.path.abspath(__file__ + '../../../tests/resources')
        try:
            with warnings.catch_warnings():
                warnings.simplefilter('ignore')
                with open(os.devnull, 'w') as devnull:
                    with contextlib.redirect_stdout(devnull):
                        setup({}, arpes_root=phony_datasets)

        except Exception as e: # pylint: disable=broad-except
            return str(e)

        return None

    checks = [
        ('Igor Pro Support', verify_igor_pro,),
        ('Bokeh Support', verify_bokeh,),
        ('qt_tool Support', verify_qt_tool,),
        ('Import almost everything in PyARPES', verify_everything,),
    ]

    from colorama import Fore, Style

    print('Checking...')
    for check_name, check_fn in checks:
        initial_str = '[ ] {}'.format(check_name)
        print(initial_str, end='', flush=True)

        failure_message = check_fn()

        print('\b' * len(initial_str) + ' ' * len(initial_str) + '\b' * len(initial_str), end='')

        if failure_message is None:
            print('{}[✔] {}{}'.format(Fore.GREEN, check_name, Style.RESET_ALL))
        else:
            print('{}[✘] {}: \n\t{}{}'.format(Fore.RED, check_name, failure_message, Style.RESET_ALL))


def setup(outer_globals, arpes_root=None):
    """
    Performs standard imports similar to what might be achieved by specifying a reasonable IPython startup file.

    Consider this a "basic" configuration function for those that do not want to deal with IPython configuration
    themselves.

    As a bonus, this file tracks with the repository so that function moves should happen fairly transparently, and new
    functionality becomes "automatically" available.

    :param outer_globals: Globals for the calling module scope, this should be provided by calling setup(globals(), ...)
    :param arpes_root: Location of the analysis directory you are working in, as generated by
    :return:
    """

    import os

    if arpes_root is None and os.getenv('ARPES_ROOT') is None:
        raise ValueError('You must supply the location of your analysis directory.')
    if arpes_root is not None:
        os.environ['ARPES_ROOT'] = arpes_root

    import arpes.config
    arpes.config.update_configuration(user_path=os.environ['ARPES_ROOT'])

    from importlib import import_module

    def global_import_from(module_name, attributes):
        if not isinstance(attributes, list):
            attributes = [attributes]

        mod = import_module(module_name)
        for attr in attributes:
            outer_globals[attr] = getattr(mod, attr)

    def global_import(module_name, short=None):
        if short is None:
            short = module_name
        outer_globals[module_name] = import_module(module_name)

    def global_import_star(module_name):
        mod = import_module(module_name)

        if '__all__' in mod.__dict__:
            names = mod.__dict__['__all__']
        else:
            names = [x for x in mod.__dict__ if not x.startswith('_') and x not in globals()]

        outer_globals.update({k: getattr(mod, k) for k in names})

    global_import('xarray', 'xr')
    global_import('scipy')
    global_import('numpy', 'np')
    global_import('pandas', 'pd')

    global_import('matplotlib.pyplot', 'plt')

    global_import_from('matplotlib', 'colors')

    global_import('scipy.ndimage', 'ndi')

    import os.path
    outer_globals['os'] = os

    global_import('bokeh')
    global_import_from('arpes.config', ['CONFIG', 'FIGURE_PATH'])

    global_import_from('arpes.laue', 'load_laue')

    global_import_star('arpes.analysis')
    global_import_star('arpes.fits')
    global_import_star('arpes.io')

    global_import_star('arpes.plotting')

    try:
        global_import_from('arpes.plotting.qt_tool', 'qt_tool')
    except ImportError:
        print('You will need to install PyQt5 in order to make `qt_tool` available.')

    global_import_star('arpes.plotting.annotations')

    global_import_star('arpes.repair')
    global_import_star('arpes.preparation')
    global_import_star('arpes.bootstrap')
    global_import_from('arpes.utilities.autoprep', 'prepare_raw_files')

    global_import_star('arpes.analysis.band_analysis_utils')
    global_import_from('arpes.corrections', 'fermi_edge_corrections')

    import arpes.xarray_extensions  # Ensure that extensions get loaded

    global_import_from('arpes.endstations', 'load_scan')
    global_import_from('arpes.utilities', ['clean_xlsx_dataset', 'default_dataset', 'swap_reference_map'])
    global_import_star('arpes.utilities.conversion')
    global_import_star('arpes.utilities.conversion.forward')
    global_import_from('arpes.endstations', ['endstation_from_alias', 'endstation_name_from_alias'])

    try:
        global_import_from('bokeh.io', 'output_notebook')
        from bokeh.io import output_notebook
    except ImportError:
        pass

    global_import('matplotlib')
    global_import_from('mpl_toolkits.axes_grid1.inset_locator', 'inset_axes')

    try:
        import matplotlib
        matplotlib.rcParams['animation.html'] = 'html5'
    except Exception: # pylint: disable=broad-except
        pass

    arpes.config.attempt_determine_workspace(permissive=True)
    arpes.config.load_plugins()

    outer_globals['ld'] = outer_globals['simple_load']

    global_import_from('pathlib', 'Path')
    global_import_from('arpes.config', 'use_tex')
    global_import('importlib')
