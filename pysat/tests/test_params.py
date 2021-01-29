#!/usr/bin/env python
# Full license can be found in License.md
# Full author list can be found in .zenodo.json file
# DOI:10.5281/zenodo.1199703
# ----------------------------------------------------------------------------
"""
tests the pysat utils area
"""

import copy
from importlib import reload
import os
import pytest
import shutil

import pysat  # required for reimporting pysat
from pysat._params import Parameters  # required for eval statements
from pysat.tests.travisci_test_class import TravisCICleanSetup


class TestBasics():
    def setup(self):
        """Runs before every method to create a clean testing setup."""
        # store current pysat directory
        self.stored_params = copy.deepcopy(pysat.params)

        # Set up default values
        pysat.params.restore_defaults()

    def teardown(self):
        """Runs after every method to clean up previous testing."""
        pysat.params = copy.deepcopy(self.stored_params)
        pysat.params.store()
        reload(pysat)

    def test_set_data_dirs_param_single(self):
        """Update pysat directory via params, single string input"""
        pysat.params['data_dirs'] = '.'
        assert pysat.params['data_dirs'] == ['.']

        # Check if next load of pysat remembers the change
        reload(pysat)
        assert pysat.params['data_dirs'] == ['.']

    def test_set_data_dirs_param_with_list(self):
        """Update pysat directories via pysat.params, list of strings"""
        pysat.params['data_dirs'] = ['.', './']
        assert pysat.params['data_dirs'] == ['.', './']

        # Check if next load of pysat remembers the change
        reload(pysat)
        assert pysat.params['data_dirs'] == ['.', './']

    def test_set_data_dir_wrong_path(self):
        """Update data_dirs with an invalid path form"""
        with pytest.raises(OSError):
            pysat.params['data_dirs'] = 'not_a_directory'

    def test_set_data_dir_bad_directory(self):
        """Ensure you can't set data_dirs to bad path"""
        with pytest.raises(OSError) as excinfo:
            pysat.params['data_dirs'] = '/fake/directory/path'
        assert str(excinfo.value).find("don't lead to a valid") >= 0

    def test_repr(self):
        """Test __repr__ method"""
        out = pysat.params.__repr__()
        assert out.find('Parameters(path=') >= 0

    def test_str(self):
        """Ensure str method works"""

        # include a user parameter as well
        pysat.params['pysat_user_test_str'] = 'We are here.'

        out = str(pysat.params)
        # Confirm start of str
        assert out.find('pysat Parameters object') >= 0

        # Confirm that default, non-default, and user values present
        assert out.find('pysat settings') > 0
        assert out.find('Standard parameters:') > 0

        assert out.find('settings (non-default)') > 0
        assert out.find('Standard parameters (no defaults):') > 0

        assert out.find('user values') > 0
        assert out.find('User parameters:') > 0

    def test_restore_defaults(self):
        """Test restore_defaults works as intended"""

        # Get default value, as per setup
        default_val = pysat.params['update_files']

        # Change value to non-default
        pysat.params['update_files'] = not default_val

        # Restore defaults
        pysat.params.restore_defaults()

        # Ensure new value is the default
        assert pysat.params['update_files'] == default_val

        # make sure that non-default values left as is
        assert pysat.params['data_dirs'] != []

    def test_update_standard_value(self):
        """Modify a pre-existing standard parameter value and ensure stored"""

        # Get default value, as per setup
        default_val = pysat.params['update_files']

        # Change value to non-default
        pysat.params['update_files'] = not pysat.params['update_files']

        # Ensure it is in memory
        assert pysat.params['update_files'] is not default_val

        # Get a new parameters instance and verify information is retained.
        # Using eval to ensure all settings with current pysat.params retained.
        new_params = eval(pysat.params.__repr__())
        assert new_params['update_files'] == pysat.params['update_files']

    def test_no_update_user_modules(self):
        """Ensure user_modules not modifiable via params"""

        # Attempt to change value
        with pytest.raises(ValueError) as err:
            pysat.params['user_modules'] = {}
        assert str(err).find('The pysat.utils.registry ') >= 0

    def test_add_user_parameter(self):
        """Add custom parameter and ensure present"""

        pysat.params['hi_there'] = 'hello there!'
        assert pysat.params['hi_there'] == 'hello there!'

        # Get a new parameters instance and verify information is retained
        # Using eval to ensure all settings with current pysat.params retained.
        new_params = eval(pysat.params.__repr__())
        assert new_params['hi_there'] == pysat.params['hi_there']

    def test_clear_and_restart(self):
        """Verify clear_and_restart method impacts all values"""

        pysat.params.clear_and_restart()

        # check default value
        assert pysat.params['user_modules'] == {}

        # check value without working default
        assert pysat.params['data_dirs'] == []

        return

    def test_bad_path_instantiation(self):
        """Ensure you can't use bad path when loading Parameters"""
        with pytest.raises(OSError) as excinfo:
            Parameters(path='./made_up_name')
        assert str(excinfo.value).find("Supplied path does not exist") >= 0


class TestCIonly(TravisCICleanSetup):
    """Tests where we mess with local settings.
    These only run in CI environments such as Travis and Appveyor to avoid
    breaking an end user's setup
    """

    # Set setup/teardown to the class defaults
    setup = TravisCICleanSetup.setup
    teardown = TravisCICleanSetup.teardown

    def test_settings_file_must_be_present(self, capsys):
        """Ensure pysat_settings.json must be present"""

        reload(pysat)

        captured = capsys.readouterr()
        # Ensure pysat is running in 'first-time' mode
        assert captured.out.find("Hi there!") >= 0

        # Remove pysat settings file
        shutil.move(os.path.join(self.root, 'pysat_settings.json'),
                    os.path.join(self.root, 'pysat_settings_moved.json'))

        # Ensure we can't create a parameters file without valid .json
        with pytest.raises(RuntimeError) as err:
            Parameters()
        assert str(err).find('pysat is unable to locate a user settings') >= 0

        shutil.move(os.path.join(self.root, 'pysat_settings_moved.json'),
                    os.path.join(self.root, 'pysat_settings.json'))

    def test_settings_file_cwd(self, capsys):
        """Test Parameters works when settings file in current working dir"""

        reload(pysat)

        captured = capsys.readouterr()
        # Ensure pysat is running in 'first-time' mode
        assert captured.out.find("Hi there!") >= 0

        # Move pysat settings file to cwd
        shutil.move(os.path.join(self.root, 'pysat_settings.json'),
                    os.path.join('./', 'pysat_settings.json'))

        # Try loading by supplying a specific path
        test_params = Parameters(path='./')

        # Supplying no path should yield the same result
        test_params2 = Parameters()

        # Confirm data is the same for both
        assert test_params.data == test_params2.data

        # Confirm path is the same for both
        assert test_params.file_path == test_params2.file_path

        # Ensure we didn't load a file in .pysat
        assert not os.path.isfile(os.path.join(self.root,
                                               'pysat_settings.json'))

        # Move pysat settings file back to original
        shutil.move(os.path.join('./', 'pysat_settings.json'),
                    os.path.join(self.root, 'pysat_settings.json'))
