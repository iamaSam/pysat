# -*- coding: utf-8 -*-
"""Supports the SEE instrument on TIMED.

Downloads data from the NASA Coordinated Data
Analysis Web (CDAWeb).

Supports two options for loading that may be
specified at instantiation.

.. deprecated:: 2.3.0
  This Instrument module has been removed from pysat in the 3.0.0 release and
  can now be found in pysatIncubator (https://github.com/pysat/pysatNASA)

Properties
----------
platform
    'timed'
name
    'see'
tag
    None
sat_id
    None supported
flatten_twod
    If True, then two dimensional data is flattened across
    columns. Name mangling is used to group data, first column
    is 'name', last column is 'name_end'. In between numbers are
    appended 'name_1', 'name_2', etc. All data for a given 2D array
    may be accessed via, data.loc[:, 'item':'item_end']
    If False, then 2D data is stored as a series of DataFrames,
    indexed by Epoch. data.loc[0, 'item']
    (default=True)


Note
----
- no tag required


Warnings
--------
- Currently no cleaning routine.

"""

from __future__ import print_function
from __future__ import absolute_import
import functools
import warnings

import pysat
from pysat.instruments.methods import nasa_cdaweb as cdw
from pysat.instruments.methods import general as mm_gen

# include basic instrument info
platform = 'timed'
name = 'see'
tags = {'': ''}
sat_ids = {'': ['']}
_test_dates = {'': {'': pysat.datetime(2009, 1, 1)}}


# support list files routine
# use the default CDAWeb method
fname = 'timed_l3a_see_{year:04d}{month:02d}{day:02d}_v01.cdf'
supported_tags = {'': {'': fname}}
list_files = functools.partial(mm_gen.list_files,
                               supported_tags=supported_tags,
                               fake_daily_files_from_monthly=True)

# support download routine
# use the default CDAWeb method
basic_tag = {'dir': '/pub/data/timed/see/data/level3a_cdf',
             'remote_fname': '{year:4d}/{month:02d}/'+fname,
             'local_fname': fname}
supported_tags = {'': {'': basic_tag}}
download = functools.partial(cdw.download, supported_tags)
# support listing files currently on CDAWeb
list_remote_files = functools.partial(cdw.list_remote_files,
                                      supported_tags=supported_tags)

# support load routine
# use the default CDAWeb method
load = functools.partial(cdw.load, fake_daily_files_from_monthly=True)


def init(self):
    """Initializes the Instrument object with values
    """

    warnings.warn(" ".join(["_".join([self.platform, self.name]),
                            "has been removed from the pysat-managed",
                            "Instruments in pysat 3.0.0, and now resides in",
                            "pysatNASA:",
                            "https://github.com/pysat/pysatNASA"]),
                  DeprecationWarning, stacklevel=2)
    return


def clean(inst):
    """Routine to return TIMED SEE data cleaned to the specified level

    Parameters
    ----------
    inst : pysat.Instrument
        Instrument class object, whose attribute clean_level is used to return
        the desired level of data selectivity.

    Note
    ----
    No cleaning currently available.

    """

    return None
