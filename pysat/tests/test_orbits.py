import datetime as dt
from dateutil.relativedelta import relativedelta
import numpy as np

import pandas as pds
# Orbits period is a pandas.Timedelta kwarg, and the pandas repr
# does not include a module name. Import required to run eval
# on Orbit representation
from pandas import Timedelta  # noqa: F401
import pytest

import pysat


def filter_data(inst, times=None):
    """Remove data from instrument, simulating gaps in the dataset."""

    if times is None:
        times = [[dt.datetime(2009, 1, 1, 1, 37),
                  dt.datetime(2009, 1, 1, 3, 14)],
                 [dt.datetime(2009, 1, 1, 10), dt.datetime(2009, 1, 1, 12)],
                 [dt.datetime(2009, 1, 1, 22), dt.datetime(2009, 1, 2, 2)],
                 [dt.datetime(2009, 1, 13), dt.datetime(2009, 1, 15)],
                 [dt.datetime(2009, 1, 20, 1), dt.datetime(2009, 1, 25, 23)],
                 [dt.datetime(2009, 1, 25, 23, 30),
                  dt.datetime(2009, 1, 26, 3)]]

    for time in times:
        idx, = np.where((inst.index > time[1]) | (inst.index < time[0]))
        inst.data = inst[idx]

    return


class TestOrbitsUserInterface():
    """Tests the user interface for orbits, including error handling."""

    def setup(self):
        """Set up User Interface unit tests."""
        self.in_args = ['pysat', 'testing']
        self.in_kwargs = {'clean_level': 'clean', 'update_files': True}
        self.testInst = None
        self.stime = dt.datetime(2009, 1, 1)
        return

    def teardown(self):
        """Tear down User Interface tests."""
        del self.in_args, self.in_kwargs, self.testInst, self.stime
        return

    def test_orbit_w_bad_kind(self):
        """Test orbit failure with bad 'kind' input."""
        self.in_kwargs['orbit_info'] = {'index': 'mlt', 'kind': 'cats'}
        with pytest.raises(ValueError):
            self.testInst = pysat.Instrument(*self.in_args, **self.in_kwargs)
        return

    @pytest.mark.parametrize("info", [({'index': 'magnetic local time',
                                        'kind': 'longitude'}),
                                      (None),
                                      ({'index': 'magnetic local time',
                                        'kind': 'lt'}),
                                      ({'index': 'magnetic local time',
                                       'kind': 'polar'}),
                                      ({'index': 'magnetic local time',
                                        'kind': 'orbit'})])
    def test_orbit_w_bad_orbit_info(self, info):
        """Test orbit failure on iteration with orbit initialization."""
        self.in_kwargs['orbit_info'] = info
        self.testInst = pysat.Instrument(*self.in_args, **self.in_kwargs)
        self.testInst.load(date=self.stime)

        with pytest.raises(ValueError):
            self.testInst.orbits.next()
        return

    @pytest.mark.parametrize("info", [({'index': 'magnetic local time',
                                        'kind': 'polar'}),
                                      ({'index': 'magnetic local time',
                                        'kind': 'orbit'}),
                                      ({'index': 'magnetic local time',
                                        'kind': 'longitude'}),
                                      ({'index': 'magnetic local time',
                                        'kind': 'lt'})])
    def test_orbit_polar_w_missing_orbit_index(self, info):
        """Test orbit failure oon iteration with missing orbit index."""
        self.in_kwargs['orbit_info'] = info
        self.testInst = pysat.Instrument(*self.in_args, **self.in_kwargs)

        # Force index to None beforee loading and iterating
        self.testInst.orbits.orbit_index = None
        self.testInst.load(date=self.stime)
        with pytest.raises(ValueError):
            self.testInst.orbits.next()
        return

    def test_orbit_repr(self):
        """Test the Orbit representation."""
        self.in_kwargs['orbit_info'] = {'index': 'mlt'}
        self.testInst = pysat.Instrument(*self.in_args, **self.in_kwargs)
        out_str = self.testInst.orbits.__repr__()

        assert out_str.find("Orbits(") >= 0
        return

    def test_orbit_str(self):
        """Test the Orbit string representation with data."""
        self.in_kwargs['orbit_info'] = {'index': 'mlt'}
        self.testInst = pysat.Instrument(*self.in_args, **self.in_kwargs)
        self.testInst.load(date=self.stime)
        out_str = self.testInst.orbits.__str__()

        assert out_str.find("Orbit Settings") >= 0
        assert out_str.find("Orbit Lind: local time") < 0
        return


class TestSpecificUTOrbits():
    """Run the tests for specific behaviour in the MLT orbits."""

    def setup(self):
        """Runs before every method to create a clean testing setup."""
        self.testInst = pysat.Instrument('pysat', 'testing',
                                         clean_level='clean',
                                         orbit_info={'index': 'mlt'},
                                         update_files=True)
        self.stime = pysat.instruments.pysat_testing._test_dates['']['']
        self.inc_min = 97
        self.etime = None
        return

    def teardown(self):
        """Runs after every method to clean up previous testing."""
        del self.testInst, self.stime, self.inc_min, self.etime
        return

    @pytest.mark.parametrize('orbit_inc', [(0), (1), (-1), (-2), (14)])
    def test_single_orbit_call_by_index(self, orbit_inc):
        """Test successful orbit call by index."""
        # Load the data
        self.testInst.load(date=self.stime)
        self.testInst.orbits[orbit_inc]

        # Increment the time
        if orbit_inc >= 0:
            self.stime += dt.timedelta(minutes=orbit_inc * self.inc_min)
        else:
            self.stime += dt.timedelta(minutes=self.inc_min
                                       * (np.ceil(1440.0 / self.inc_min)
                                          + orbit_inc))
        self.etime = self.stime + dt.timedelta(seconds=(self.inc_min * 60 - 1))

        # Test the time
        assert (self.testInst.index[0] == self.stime)
        assert (self.testInst.index[-1] == self.etime)
        return

    @pytest.mark.parametrize("orbit_ind,raise_err", [(17, Exception),
                                                     (None, TypeError)])
    def test_single_orbit_call_bad_index(self, orbit_ind, raise_err):
        """Test orbit failure with bad index."""
        self.testInst.load(date=self.stime)
        with pytest.raises(raise_err):
            self.testInst.orbits[orbit_ind]
        return

    def test_oribt_number_via_current_multiple_orbit_calls_in_day(self):
        """Test orbit number with multiple orbits calls in a day."""
        self.testInst.load(date=self.stime)
        self.testInst.bounds = (self.stime, None)
        true_vals = np.arange(15)
        true_vals[-1] = 0
        test_vals = []
        for i, inst in enumerate(self.testInst.orbits):
            if i > 14:
                break
            test_vals.append(inst.orbits.current)
            assert inst.orbits.current == self.testInst.orbits.current

        assert np.all(test_vals == true_vals)
        return

    def test_all_single_orbit_calls_in_day(self):
        """Test all single orbit calls in a day."""
        self.testInst.load(date=self.stime)
        self.testInst.bounds = (self.stime, None)
        for i, inst in enumerate(self.testInst.orbits):
            if i > 14:
                break

            # Test the start index
            self.etime = self.stime + i * relativedelta(minutes=self.inc_min)
            assert inst.index[0] == self.etime
            assert self.testInst.index[0] == self.etime

            # Test the end index
            self.etime += relativedelta(seconds=((self.inc_min * 60) - 1))
            assert inst.index[-1] == self.etime
            assert self.testInst.index[-1] == self.etime
        return

    def test_orbit_next_call_no_loaded_data(self):
        """Test orbit next call without loading data."""
        self.testInst.orbits.next()
        assert (self.testInst.index[0] == dt.datetime(2008, 1, 1))
        assert (self.testInst.index[-1] == dt.datetime(2008, 1, 1, 0, 38, 59))
        return

    def test_orbit_prev_call_no_loaded_data(self):
        """Test orbit previous call without loading data."""
        self.testInst.orbits.prev()
        # this isn't a full orbit
        assert (self.testInst.index[-1]
                == dt.datetime(2010, 12, 31, 23, 59, 59))
        assert (self.testInst.index[0] == dt.datetime(2010, 12, 31, 23, 49))
        return

    def test_single_orbit_call_orbit_starts_0_UT_using_next(self):
        """Test orbit next call with data."""
        self.testInst.load(date=self.stime)
        self.testInst.orbits.next()
        self.etime = self.stime + dt.timedelta(seconds=(self.inc_min * 60 - 1))
        assert (self.testInst.index[0] == self.stime)
        assert (self.testInst.index[-1] == self.etime)
        return

    def test_single_orbit_call_orbit_starts_0_UT_using_prev(self):
        """Test orbit prev call with data."""
        self.testInst.load(date=self.stime)
        self.testInst.orbits.prev()
        self.stime += 14 * relativedelta(minutes=self.inc_min)
        self.etime = self.stime + dt.timedelta(seconds=((self.inc_min * 60)
                                                        - 1))
        assert self.testInst.index[0] == self.stime
        assert self.testInst.index[-1] == self.etime
        return

    def test_single_orbit_call_orbit_starts_off_0_UT_using_next(self):
        """Test orbit next call with data for previous day."""
        self.stime -= dt.timedelta(days=1)
        self.testInst.load(date=self.stime)
        self.testInst.orbits.next()
        assert (self.testInst.index[0] == dt.datetime(2008, 12, 30, 23, 45))
        assert (self.testInst.index[-1]
                == (dt.datetime(2008, 12, 30, 23, 45)
                    + relativedelta(seconds=(self.inc_min * 60 - 1))))
        return

    def test_single_orbit_call_orbit_starts_off_0_UT_using_prev(self):
        """Test orbit previous call with data for previous day."""
        self.stime -= dt.timedelta(days=1)
        self.testInst.load(date=self.stime)
        self.testInst.orbits.prev()
        assert (self.testInst.index[0]
                == (dt.datetime(2009, 1, 1)
                    - relativedelta(minutes=self.inc_min)))
        assert (self.testInst.index[-1]
                == (dt.datetime(2009, 1, 1) - relativedelta(seconds=1)))
        return


class TestGeneralOrbitsMLT():
    """Run the general orbit tests by MLT for pandas."""

    def setup(self):
        """Runs before every method to create a clean testing setup."""
        self.testInst = pysat.Instrument('pysat', 'testing',
                                         clean_level='clean',
                                         orbit_info={'index': 'mlt'},
                                         update_files=True)
        self.stime = pysat.instruments.pysat_testing._test_dates['']['']
        return

    def teardown(self):
        """Runs after every method to clean up previous testing."""
        del self.testInst, self.stime
        return

    def test_equality_with_copy(self):
        """Test that copy is the same as original."""
        self.out = self.testInst.orbits.copy()
        assert self.out == self.testInst.orbits
        return

    def test_equality_with_data_with_copy(self):
        """Test that copy is the same as original if data is loaded."""
        # Load data
        self.testInst.load(date=self.stime)

        # Load up an orbit
        self.testInst.orbits[0]
        self.out = self.testInst.orbits.copy()

        assert self.out == self.testInst.orbits
        return

    def test_inequality_different_data(self):
        """Test that equality is false if different data."""
        # Load data
        self.testInst.load(date=self.stime)

        # Load up an orbit
        self.testInst.orbits[0]

        # Make copy
        self.out = self.testInst.orbits.copy()

        # Modify data
        self.out._full_day_data = self.testInst._null_data

        assert self.out != self.testInst.orbits
        return

    def test_inequality_modified_object(self):
        """Test that equality is false if other missing attributes."""
        self.out = self.testInst.orbits.copy()

        # Remove attribute
        del self.out.orbit_index

        assert self.testInst.orbits != self.out
        return

    def test_inequality_reduced_object(self):
        """Test that equality is false if self missing attributes."""
        self.out = self.testInst.orbits.copy()
        self.out.hi_there = 'hi'
        assert self.testInst.orbits != self.out
        return

    def test_inequality_different_type(self):
        """Test that equality is false if different type."""
        assert self.testInst.orbits != self.testInst
        return

    def test_eval_repr(self):
        """Test eval of repr recreates object."""
        # eval and repr don't play nice for custom functions
        if len(self.testInst.custom_functions) != 0:
            self.testInst.custom_clear()

        self.out = eval(self.testInst.orbits.__repr__())
        assert self.out == self.testInst.orbits
        return

    def test_repr_and_copy(self):
        """Test repr consistent with object copy."""
        # Not tested with eval due to issues with datetime
        self.out = self.testInst.orbits.__repr__()
        second_out = self.testInst.orbits.copy().__repr__()
        assert self.out == second_out
        return

    def test_load_orbits_w_empty_data(self):
        """Test orbit loading outside of the instrument data range."""
        self.stime -= dt.timedelta(days=365 * 100)
        self.testInst.load(date=self.stime)
        self.testInst.orbits[0]
        with pytest.raises(StopIteration):
            self.testInst.orbits.next()
        return

    def test_less_than_one_orbit_of_data(self):
        """Test successful load with less than one orbit of data."""
        def truncate_data(inst):
            """Local helper function to reduce available data."""
            inst.data = inst[0:20]

        self.testInst.custom_attach(truncate_data)
        self.testInst.load(date=self.stime)
        self.testInst.orbits.next()

        # a recursion issue has been observed in this area
        # checking for date to limit reintroduction potential
        assert self.testInst.date == self.stime
        # store comparison data
        saved_data = self.testInst.copy()
        self.testInst.load(date=self.stime)
        self.testInst.orbits[0]
        assert all(self.testInst.data == saved_data.data)
        d1check = self.testInst.date == saved_data.date
        assert d1check
        return

    def test_less_than_one_orbit_of_data_four_ways_two_days(self):
        """Test successful loading of different partial orbits."""
        # create situation where the < 1 orbit split across two days
        def manual_orbits(inst):
            """Local function for breaking up orbits."""
            if inst.date == dt.datetime(2009, 1, 5):
                inst.data = inst[0:20]
            elif inst.date == dt.datetime(2009, 1, 4):
                inst.data = inst[-20:]
            return

        self.testInst.custom_attach(manual_orbits)
        self.stime += dt.timedelta(days=3)
        self.testInst.load(date=self.stime)

        # starting from no orbit calls next loads first orbit
        self.testInst.orbits.next()

        # store comparison data
        saved_data = self.testInst.copy()
        self.testInst.load(date=self.stime + dt.timedelta(days=1))
        self.testInst.orbits[0]
        if self.testInst.orbits.num == 1:
            # equivalence only when only one orbit
            # some test settings can violate this assumption
            assert all(self.testInst.data == saved_data.data)

        self.testInst.load(date=self.stime)
        self.testInst.orbits[0]
        assert all(self.testInst.data == saved_data.data)

        self.testInst.load(date=self.stime + dt.timedelta(days=1))
        self.testInst.orbits.prev()
        if self.testInst.orbits.num == 1:
            assert all(self.testInst.data == saved_data.data)

        # a recursion issue has been observed in this area
        # checking for date to limit reintroduction potential
        d1check = self.testInst.date == saved_data.date
        assert d1check
        return

    @pytest.mark.parametrize("iterations", [(10), (20)])
    def test_repeated_orbit_calls(self, iterations):
        """Test that repeated orbit calls are reversible."""
        self.testInst.load(date=self.stime)
        self.testInst.orbits.next()
        control = self.testInst.copy()
        n_time = []
        p_time = []
        for j in range(iterations):
            n_time.append(self.testInst.index[0])
            self.testInst.orbits.next()
        for j in range(iterations):
            self.testInst.orbits.prev()
            p_time.append(self.testInst.index[0])
        assert all(control.data == self.testInst.data)
        assert np.all(p_time == n_time[::-1])
        return

    @pytest.mark.parametrize("iterations", [(10), (20)])
    def test_repeated_orbit_calls_alternative(self, iterations):
        """Test repeated orbit calls are reversible using alternate pattern."""
        self.testInst.load(date=self.stime)
        self.testInst.orbits.next()
        control = self.testInst.copy()
        for j in range(iterations):
            self.testInst.orbits.next()
        for j in range(2 * iterations):
            self.testInst.orbits.prev()
        for j in range(iterations):
            self.testInst.orbits.next()
        assert all(control.data == self.testInst.data)
        return


class TestGeneralOrbitsMLTxarray(TestGeneralOrbitsMLT):
    """Run the general orbit tests by MLT for xarray."""

    def setup(self):
        """Runs before every method to create a clean testing setup."""
        self.testInst = pysat.Instrument('pysat', 'testing_xarray',
                                         clean_level='clean',
                                         orbit_info={'index': 'mlt'},
                                         update_files=True)
        self.stime = pysat.instruments.pysat_testing_xarray._test_dates['']['']
        return

    def teardown(self):
        """Runs after every method to clean up previous testing."""
        del self.testInst, self.stime
        return


class TestGeneralOrbitsNonStandardIteration():
    """ Tests for non standard data setups

    Note
    ----
    Create an iteration window that is larger than step size.
    Ensure the overlapping data doesn't end up in the orbit iteration.

    """

    def setup(self):
        """Runs before every method to create a clean testing setup."""
        self.testInst = pysat.Instrument('pysat', 'testing',
                                         clean_level='clean',
                                         orbit_info={'index': 'mlt'},
                                         update_files=True)
        self.testInst.bounds = (self.testInst.files.files.index[0],
                                self.testInst.files.files.index[11],
                                '2D', dt.timedelta(days=3))
        self.orbit_starts = []
        self.orbit_stops = []
        return

    def teardown(self):
        """Runs after every method to clean up previous testing."""
        del self.testInst, self.orbit_starts, self.orbit_stops
        return

    def test_no_orbit_overlap_with_overlapping_iteration(self):
        """Ensure error when overlap in iteration data."""
        with pytest.raises(ValueError):
            self.testInst.orbits.next()
        return

    @pytest.mark.parametrize("bounds_type", ['by_date', 'by_file'])
    def test_no_orbit_overlap_with_nonoverlapping_iteration(self, bounds_type):
        """Ensure orbit data does not overlap when overlap in iteration data."""

        if bounds_type == 'by_date':
            bounds = (self.testInst.files.files.index[0],
                      self.testInst.files.files.index[11],
                      '2D', dt.timedelta(days=2))
        elif bounds_type == 'by_file':
            bounds = (self.testInst.files[0], self.testInst.files[11], 2, 2)

        self.testInst.bounds = bounds

        for inst in self.testInst.orbits:
            self.orbit_starts.append(inst.index[0])
            self.orbit_stops.append(inst.index[-1])
        self.orbit_starts = pds.Series(self.orbit_starts)
        self.orbit_stops = pds.Series(self.orbit_stops)
        assert self.orbit_starts.is_monotonic_increasing
        assert self.orbit_stops.is_monotonic_increasing
        return


class TestGeneralOrbitsLong(TestGeneralOrbitsMLT):
    """Run the general orbit tests by Longitude for pandas."""

    def setup(self):
        """Runs before every method to create a clean testing setup."""
        self.testInst = pysat.Instrument('pysat', 'testing',
                                         clean_level='clean',
                                         orbit_info={'index': 'longitude',
                                                     'kind': 'longitude'},
                                         update_files=True)
        self.stime = pysat.instruments.pysat_testing._test_dates['']['']
        return

    def teardown(self):
        """Runs after every method to clean up previous testing."""
        del self.testInst, self.stime
        return


class TestGeneralOrbitsLongXarray(TestGeneralOrbitsMLT):
    """Run the general orbit tests by Longitude for xarray."""

    def setup(self):
        """Runs before every method to create a clean testing setup."""
        self.testInst = pysat.Instrument('pysat', 'testing_xarray',
                                         clean_level='clean',
                                         orbit_info={'index': 'longitude',
                                                     'kind': 'longitude'},
                                         update_files=True)
        self.stime = pysat.instruments.pysat_testing._test_dates['']['']
        return

    def teardown(self):
        """Runs after every method to clean up previous testing."""
        del self.testInst, self.stime
        return


class TestGeneralOrbitsOrbitNumber(TestGeneralOrbitsMLT):
    """Run the general orbit tests by Orbit Number for pandas."""

    def setup(self):
        """Runs before every method to create a clean testing setup."""
        self.testInst = pysat.Instrument('pysat', 'testing',
                                         clean_level='clean',
                                         orbit_info={'index': 'orbit_num',
                                                     'kind': 'orbit'},
                                         update_files=True)
        self.stime = pysat.instruments.pysat_testing._test_dates['']['']
        return

    def teardown(self):
        """Runs after every method to clean up previous testing."""
        del self.testInst, self.stime
        return


class TestGeneralOrbitsOrbitNumberXarray(TestGeneralOrbitsMLT):
    """Run the general orbit tests by Orbit Number for xarray."""

    def setup(self):
        """Runs before every method to create a clean testing setup."""
        self.testInst = pysat.Instrument('pysat', 'testing_xarray',
                                         clean_level='clean',
                                         orbit_info={'index': 'orbit_num',
                                                     'kind': 'orbit'},
                                         update_files=True)
        self.stime = pysat.instruments.pysat_testing_xarray._test_dates['']['']
        return

    def teardown(self):
        """Runs after every method to clean up previous testing."""
        del self.testInst, self.stime
        return


class TestGeneralOrbitsLatitude(TestGeneralOrbitsMLT):
    """Run the general orbit tests for orbits defined by Latitude -- pandas."""

    def setup(self):
        """Runs before every method to create a clean testing setup."""
        self.testInst = pysat.Instrument('pysat', 'testing',
                                         clean_level='clean',
                                         orbit_info={'index': 'latitude',
                                                     'kind': 'polar'},
                                         update_files=True)
        self.stime = pysat.instruments.pysat_testing._test_dates['']['']
        return

    def teardown(self):
        """Runs after every method to clean up previous testing."""
        del self.testInst, self.stime
        return


class TestGeneralOrbitsLatitudeXarray(TestGeneralOrbitsMLT):
    """Run the general orbit tests for orbits defined by Latitude -- xarray."""

    def setup(self):
        """Runs before every method to create a clean testing setup."""
        self.testInst = pysat.Instrument('pysat', 'testing_xarray',
                                         clean_level='clean',
                                         orbit_info={'index': 'latitude',
                                                     'kind': 'polar'},
                                         update_files=True)
        self.stime = pysat.instruments.pysat_testing_xarray._test_dates['']['']
        return

    def teardown(self):
        """Runs after every method to clean up previous testing."""
        del self.testInst, self.stime
        return


class TestOrbitsGappyData():
    """Run the gappy orbit tests for orbits defined by MLT -- pandas."""

    def setup(self):
        """Runs before every method to create a clean testing setup."""
        self.testInst = pysat.Instrument('pysat', 'testing',
                                         clean_level='clean',
                                         orbit_info={'index': 'mlt'},
                                         update_files=True)
        self.testInst.custom_attach(filter_data)
        self.stime = pysat.instruments.pysat_testing._test_dates['']['']
        return

    def teardown(self):
        """Runs after every method to clean up previous testing."""
        del self.testInst, self.stime
        return

    def test_repeat_orbit_calls_sym_multi_day_0_UT_really_long_time_gap(self):
        """Test successful orbit calls over a multi-day gap."""
        self.testInst.load(date=dt.datetime(2009, 1, 19))
        self.testInst.orbits.next()
        control = self.testInst.copy()
        for j in range(45):
            self.testInst.orbits.next()
        for j in range(45):
            self.testInst.orbits.prev()
        assert all(control.data == self.testInst.data)
        return

    @pytest.mark.parametrize("day", [1, 25])
    def test_repeat_orbit_calls_cutoffs_with_gaps(self, day):
        """Test that orbits are selected at same cutoffs when reversed."""
        self.testInst.load(date=dt.datetime(2009, 1, day))
        self.testInst.orbits.next()
        control = self.testInst.copy()
        n_time = []
        p_time = []
        for j in range(20):
            n_time.append(self.testInst.index[0])
            self.testInst.orbits.next()

        for j in range(20):
            self.testInst.orbits.prev()
            p_time.append(self.testInst.index[0])

        check = np.all(p_time == n_time[::-1])
        assert all(control.data == self.testInst.data) & check
        return


class TestOrbitsGappyDataXarray(TestOrbitsGappyData):
    """Run the gappy orbit tests for orbits defined by MLT -- xarray."""

    def setup(self):
        """Runs before every method to create a clean testing setup."""
        self.testInst = pysat.Instrument('pysat', 'testing_xarray',
                                         clean_level='clean',
                                         orbit_info={'index': 'mlt'},
                                         update_files=True)
        self.testInst.custom_attach(filter_data)
        self.stime = pysat.instruments.pysat_testing._test_dates['']['']
        return

    def teardown(self):
        """Runs after every method to clean up previous testing."""
        del self.testInst, self.stime
        return


class TestOrbitsGappyData2():
    """Run additional gappy orbit tests for orbits defined by MLT -- pandas."""

    def setup(self):
        """Runs before every method to create a clean testing setup."""
        self.testInst = pysat.Instrument('pysat', 'testing',
                                         clean_level='clean',
                                         orbit_info={'index': 'mlt'})
        self.stime = pysat.instruments.pysat_testing._test_dates['']['']
        times = [[dt.datetime(2008, 12, 31, 4),
                  dt.datetime(2008, 12, 31, 5, 37)],
                 [dt.datetime(2009, 1, 1),
                  dt.datetime(2009, 1, 1, 1, 37)]]
        for seconds in np.arange(38):
            day = (dt.datetime(2009, 1, 2)
                   + dt.timedelta(days=int(seconds)))
            times.append([day, day
                          + dt.timedelta(hours=1, minutes=37,
                                         seconds=int(seconds))
                          - dt.timedelta(seconds=20)])

        self.testInst.custom_attach(filter_data, kwargs={'times': times})
        return

    def teardown(self):
        """Runs after every method to clean up previous testing."""
        del self.testInst, self.stime
        return

    def test_repeated_orbit_calls_alternative(self):
        """Test repeated orbit calls are reversible"""
        self.testInst.load(date=self.stime)
        self.testInst.orbits.next()
        control = self.testInst.copy()
        for j in range(20):
            self.testInst.orbits.next()
        for j in range(40):
            self.testInst.orbits.prev()
        for j in range(20):
            self.testInst.orbits.next()
        assert all(control.data == self.testInst.data)
        return


class TestOrbitsGappyData2Xarray(TestOrbitsGappyData2):
    """Run additional gappy orbit tests for orbits defined by MLT -- xarray"""

    def setup(self):
        """Runs before every method to create a clean testing setup."""
        self.testInst = pysat.Instrument('pysat', 'testing_xarray',
                                         clean_level='clean',
                                         orbit_info={'index': 'mlt'})
        self.stime = pysat.instruments.pysat_testing._test_dates['']['']
        times = [[dt.datetime(2008, 12, 31, 4),
                  dt.datetime(2008, 12, 31, 5, 37)],
                 [dt.datetime(2009, 1, 1),
                  dt.datetime(2009, 1, 1, 1, 37)]]
        for seconds in np.arange(38):
            day = (dt.datetime(2009, 1, 2)
                   + dt.timedelta(days=int(seconds)))
            times.append([day, day
                          + dt.timedelta(hours=1, minutes=37,
                                         seconds=int(seconds))
                          - dt.timedelta(seconds=20)])

        self.testInst.custom_attach(filter_data, kwargs={'times': times})
        return

    def teardown(self):
        """Runs after every method to clean up previous testing."""
        del self.testInst, self.stime
        return


class TestOrbitsGappyLongData(TestOrbitsGappyData):
    """Run the gappy orbit tests for orbits defined by Longitude -- pandas"""

    def setup(self):
        """Runs before every method to create a clean testing setup."""
        self.testInst = pysat.Instrument('pysat', 'testing',
                                         clean_level='clean',
                                         orbit_info={'index': 'longitude',
                                                     'kind': 'longitude'})

        self.testInst.custom_attach(filter_data)
        self.stime = pysat.instruments.pysat_testing._test_dates['']['']
        return

    def teardown(self):
        """Runs after every method to clean up previous testing."""
        del self.testInst, self.stime
        return


class TestOrbitsGappyLongDataXarray(TestOrbitsGappyData):
    """Run the gappy orbit tests for orbits defined by Longitude -- xarray"""

    def setup(self):
        """Runs before every method to create a clean testing setup."""
        self.testInst = pysat.Instrument('pysat', 'testing_xarray',
                                         clean_level='clean',
                                         orbit_info={'index': 'longitude',
                                                     'kind': 'longitude'})
        self.testInst.custom_attach(filter_data)
        self.stime = pysat.instruments.pysat_testing._test_dates['']['']
        return

    def teardown(self):
        """Runs after every method to clean up previous testing."""
        del self.testInst, self.stime
        return


class TestOrbitsGappyOrbitNumData(TestOrbitsGappyData):
    """Run the gappy orbit tests for orbits defined by Orbit Number -- pandas"""

    def setup(self):
        """Runs before every method to create a clean testing setup."""
        self.testInst = pysat.Instrument('pysat', 'testing',
                                         clean_level='clean',
                                         orbit_info={'index': 'orbit_num',
                                                     'kind': 'orbit'})
        self.testInst.custom_attach(filter_data)
        self.stime = pysat.instruments.pysat_testing._test_dates['']['']
        return

    def teardown(self):
        """Runs after every method to clean up previous testing."""
        del self.testInst, self.stime
        return


class TestOrbitsGappyOrbitNumDataXarray(TestOrbitsGappyData):
    """Run the gappy orbit tests for orbits defined by Orbit Number -- xarray"""

    def setup(self):
        """Runs before every method to create a clean testing setup."""
        self.testInst = pysat.Instrument('pysat', 'testing_xarray',
                                         clean_level='clean',
                                         orbit_info={'index': 'orbit_num',
                                                     'kind': 'orbit'})
        self.testInst.custom_attach(filter_data)
        self.stime = pysat.instruments.pysat_testing._test_dates['']['']
        return

    def teardown(self):
        """Runs after every method to clean up previous testing."""
        del self.testInst, self.stime
        return


class TestOrbitsGappyOrbitLatData(TestOrbitsGappyData):
    """Run the gappy orbit tests for orbits defined by Latitude -- pandas"""

    def setup(self):
        """Runs before every method to create a clean testing setup."""
        self.testInst = pysat.Instrument('pysat', 'testing',
                                         clean_level='clean',
                                         orbit_info={'index': 'latitude',
                                                     'kind': 'polar'})

        self.testInst.custom_attach(filter_data)
        self.stime = pysat.instruments.pysat_testing._test_dates['']['']
        return

    def teardown(self):
        """Runs after every method to clean up previous testing."""
        del self.testInst, self.stime
        return


class TestOrbitsGappyOrbitLatDataXarray(TestOrbitsGappyData):
    """Run the gappy orbit tests for orbits defined by Latitude -- xarray"""

    def setup(self):
        """Runs before every method to create a clean testing setup."""
        self.testInst = pysat.Instrument('pysat', 'testing_xarray',
                                         clean_level='clean',
                                         orbit_info={'index': 'latitude',
                                                     'kind': 'polar'})

        self.testInst.custom_attach(filter_data)
        self.stime = pysat.instruments.pysat_testing._test_dates['']['']
        return

    def teardown(self):
        """Runs after every method to clean up previous testing."""
        del self.testInst, self.stime
        return
