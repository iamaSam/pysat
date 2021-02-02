"""
pysat - Python Satellite Data Analysis Toolkit
==============================================

pysat is a package providing a simple and flexible interface for
downloading, loading, cleaning, managing, processing, and analyzing
scientific measurements. Although pysat was initially designed for
in situ satellite observations, it now supports many different types
of ground- and space-based measurements.

Main Features
-------------

- Instrument independent analysis routines.
- Instrument object providing an interface for downloading and analyzing
    a wide variety of science data sets.
    - Uses pandas or xarray for the underlying data structure; capable of
        handling the many forms scientific measurements take in a consistent
        manner.
    - Standard scientific data handling tasks (e.g., identifying, downloading,
        and loading files and cleaning and modifying data) are built into the
        Instrument object.
    - Supports metadata consistent with the netCDF CF-1.6 standard. Each
        variable has a name, long name, and units. Note units are informational
        only.
- Simplifies data management
    - Iterator support for loading data by day/file/orbit, independent of
        data storage details.
    - Orbits are calculated on the fly from loaded data and span day breaks.
    - Iterate over custom seasons
- Supports rigorous time-series calculations that require spin up/down
    time across day, orbit, and file breaks.
- Includes helper functions to reduce the barrier in adding new science
    instruments to pysat


"""

import logging
import os
from portalocker import Lock

logger = logging.getLogger(__name__)
handler = logging.StreamHandler()
formatter = logging.Formatter('%(name)s %(levelname)s: %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.WARNING)

# Import and set user and pysat parameters object
from pysat import _params

# set version
here = os.path.abspath(os.path.dirname(__file__))
version_filename = os.path.join(here, 'version.txt')

# Get home directory
home_dir = os.path.expanduser('~')

# Set pysat directory path in home directory
pysat_dir = os.path.join(home_dir, '.pysat')

# Set directory for test data
test_data_path = os.path.join(here, 'tests', 'test_data')

# Create a .pysat directory or parameters file if one doesn't exist
if not os.path.isdir(pysat_dir) or \
        (not os.path.isfile(os.path.join(pysat_dir, 'pysat_settings.json'))):

    # Make a .pysat directory if not already present
    if not os.path.isdir(pysat_dir):
        os.mkdir(pysat_dir)
        os.mkdir(os.path.join(pysat_dir, 'instruments'))
        os.mkdir(os.path.join(pysat_dir, 'instruments', 'archive'))
        print('Created .pysat directory in home directory to store settings.')

    # Create parameters file
    if not os.path.isfile(os.path.join(pysat_dir, 'pysat_settings.json')):
        params = _params.Parameters(path=pysat_dir, create_new=True)

    # Set initial data directory if we are on Travis
    if (os.environ.get('TRAVIS') == 'true'):
        data_dir = '/home/travis/build/pysatData'
        params['data_dirs'] = [data_dir]

    print(''.join(("\nHi there!  Pysat will nominally store data in the "
                   "'pysatData' directory at the user's home directory level. "
                   "Set `pysat.params['data_dirs']` equal to a path that "
                   "specifies a top-level directory to store science data.")))
else:
    # Load up existing parameters file
    params = _params.Parameters()

# Load up version information
with Lock(version_filename, 'r', params['file_timeout']) as version_file:
    __version__ = version_file.read().strip()

from pysat import utils
from pysat._constellation import Constellation
from pysat._instrument import Instrument
from pysat._meta import Meta, MetaLabels
from pysat._files import Files
from pysat._orbits import Orbits
from pysat import instruments

__all__ = ['instruments', 'utils']

# Cleanup
del here
