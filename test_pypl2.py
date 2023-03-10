import difflib
import os.path
import pathlib
import subprocess
import sys

import numpy as np

try:
    import pytest
except ImportError:
    # Utility functions in this script can also be used without test framework
    pass

if not sys.platform.startswith('win'):
    from zugbruecke import ctypes
else:
    import ctypes

from pypl2api import pl2_ad, pl2_spikes, pl2_events, pl2_info
from pypl2lib import (PyPL2FileReader)


def dump_loaded_example_data(output_filename):
    """
    Load test data and dump loaded infos and data in text files.
    """

    filename = pathlib.Path(__file__).parent / 'data' / '4chDemoPL2.pl2'
    with open(output_filename, 'w') as output_file:
        # Get file infos
        spkinfo, evtinfo, adinfo = pl2_info(filename)

        output_file.write(f'spkinfo = {spkinfo}\n')
        output_file.write(f'evtinfo = {evtinfo}\n')
        output_file.write(f'adinfo = {adinfo}\n')
        output_file.write('\n')

        # Get continuous a/d data on first channel
        ad = pl2_ad(filename, 0)
        output_file.write(f'ad = {ad}\n')
        output_file.write('\n')

        # Get spikes on first channel
        spikes = pl2_spikes(filename, 0)
        output_file.write(f'spikes = {spikes}\n')
        output_file.write('\n')

        # Get event data on all channels
        for n in range(len(evtinfo)):
            evt = pl2_events(filename, evtinfo[n].name)
            output_file.write(f'{evtinfo[n].name} = {evt}\n')
        output_file.write('\n')

        # Get strobed event data
        strobedevt = pl2_events(filename, 'Strobed')
        output_file.write(f'strobedevt = {strobedevt}\n')


def test_compare_loading_wenv_zugbruecke():
    """
    Load example data via zugbruecke and plain wenv python interpreter and
    compare dumped versions of data
    """
    # check that zugbruecke is available and test is running on non-windows
    assert not sys.platform.startswith(
        'win'), 'Test requires to run on a non-windows system to use zugbruecke'

    data_file_1 = 'dumped_example_data_using_zugbruecke.txt'
    dump_loaded_example_data(data_file_1)

    data_file_2 = 'dumped_example_data_using_wenv.txt'
    proc = subprocess.Popen(f'wenv pip install pytest', shell=True)
    proc.wait()
    cmd = f"from test_pypl2 import dump_loaded_example_data; dump_loaded_example_data(\'{data_file_2}\')"
    proc = subprocess.Popen(f'wenv python -c "{cmd}"', shell=True)
    proc.wait()

    with open(data_file_1, 'r') as file1:
        with open(data_file_2, 'r') as file2:
            # matching ration between data_file 1 and 2 has to be 1 to be identical
            matching_ratio = difflib.SequenceMatcher(None, file1.read(), file2.read()).ratio()
            assert matching_ratio == 1

    for f in (data_file_1, data_file_2):
        os.remove(f)


def assert_object_fields_are_equal(*objects):
    assert len(objects)
    assert all([o._fields_ == objects[0]._fields_ for o in objects])

    for attr_name, attr_type in objects[0]._fields_:

        values = [getattr(o, attr_name) for o in objects]

        # compare non-character arrays item-by-item
        if 'c_char' not in str(attr_type) and '_Array_' in str(attr_type):
            for idx in range(len(values[0])):
                assert all([v[idx] == values[0][idx] for v in values[1:]])
            continue

        if not all([v == values[0] for v in values[1:]]):
            print('here!')

        assert all([v == values[0] for v in values[1:]])


@pytest.fixture()
def reader():
    # Get file infos
    filename = pathlib.Path(__file__).parent / 'data' / '4chDemoPL2.pl2'
    reader = PyPL2FileReader()
    reader.pl2_open_file(filename)

    return reader


def test_compare_FileReader_SpikeChannelInfo(reader):

    for i in range(reader.pl2_file_info.m_TotalNumberOfSpikeChannels):
        # loading channel info via index, name and source methods
        channel_info_by_index = reader.pl2_get_spike_channel_info(i)

        channel_name = channel_info_by_index.m_Name
        source_id = channel_info_by_index.m_Source
        channel_id_in_source = channel_info_by_index.m_Channel

        channel_info_by_name = reader.pl2_get_spike_channel_info_by_name(channel_name)
        channel_info_by_source = reader.pl2_get_spike_channel_info_by_source(source_id,
                                                                             channel_id_in_source)

        # comparing results
        assert_object_fields_are_equal(channel_info_by_index, channel_info_by_name,
                                       channel_info_by_source)


def test_compare_FileReader_AnalogChannelInfo(reader):

    for i in range(reader.pl2_file_info.m_TotalNumberOfAnalogChannels):
        # loading channel info via index, name and source methods
        channel_info_by_index = reader.pl2_get_analog_channel_info(i)

        channel_name = channel_info_by_index.m_Name
        source_id = channel_info_by_index.m_Source
        channel_id_in_source = channel_info_by_index.m_Channel

        channel_info_by_name = reader.pl2_get_analog_channel_info_by_name(channel_name)
        channel_info_by_source = reader.pl2_get_analog_channel_info_by_source(source_id, channel_id_in_source)

        # comparing results
        assert_object_fields_are_equal(channel_info_by_index, channel_info_by_name,
                                       channel_info_by_source)


def test_compare_FileReader_DigitalChannelInfo(reader):

    for i in range(reader.pl2_file_info.m_NumberOfDigitalChannels):
        # loading channel info via index, name and source methods
        channel_info_by_index = reader.pl2_get_digital_channel_info(i)

        channel_name = channel_info_by_index.m_Name
        source_id = channel_info_by_index.m_Source
        channel_id_in_source = channel_info_by_index.m_Channel

        channel_info_by_name = reader.pl2_get_digital_channel_info_by_name(channel_name)
        channel_info_by_source = reader.pl2_get_digital_channel_info_by_source(source_id, channel_id_in_source)

        # comparing results
        assert_object_fields_are_equal(channel_info_by_index, channel_info_by_name,
                                       channel_info_by_source)


def test_compare_FileReader_spike_data(reader):

    for i in range(reader.pl2_file_info.m_TotalNumberOfSpikeChannels):
        # loading channel info via index, name and source methods
        channel_info = reader.pl2_get_spike_channel_info(i)
        channel_name = channel_info.m_Name
        source_id = channel_info.m_Source
        channel_id_in_source = channel_info.m_Channel

        # set up arguments for running spike data methods
        spike_timestamps = {}
        units = {}
        values = {}

        # run index-, name- and source-based methods to get spiking data
        res = reader.pl2_get_spike_channel_data(i)
        spike_timestamps['index'], units['index'], values['index'] = res
        res = reader.pl2_get_spike_channel_data_by_name(channel_name)
        spike_timestamps['name'], units['name'], values['name'] = res
        res = reader.pl2_get_spike_channel_data_by_source(source_id, channel_id_in_source)
        spike_timestamps['source'], units['source'], values['source'] = res

        # compare spiketimes, unit and values between methods
        np.testing.assert_array_equal(spike_timestamps['index'], spike_timestamps['name'])
        np.testing.assert_array_equal(spike_timestamps['index'], spike_timestamps['source'])

        np.testing.assert_array_equal(units['index'], units['name'])
        np.testing.assert_array_equal(units['index'], units['name'])

        np.testing.assert_array_equal(values['index'], values['name'])
        np.testing.assert_array_equal(values['index'], values['name'])


def test_compare_FileReader_digital_data(reader):

    for i in range(reader.pl2_file_info.m_NumberOfDigitalChannels):
        # loading channel info via index, name and source methods
        channel_info = reader.pl2_get_digital_channel_info(i)
        channel_name = channel_info.m_Name
        source_id = channel_info.m_Source
        channel_id_in_source = channel_info.m_Channel

        # set up arguments for runnining spike data methods
        event_timestamps = {}
        event_values = {}

        # run index-, name- and source-based methods to get digital data
        res = reader.pl2_get_digital_channel_data(i)
        event_timestamps['index'], event_values['index'] = res
        res = reader.pl2_get_digital_channel_data_by_name(channel_name)
        event_timestamps['name'], event_values['name'] = res
        res = reader.pl2_get_digital_channel_data_by_source(source_id, channel_id_in_source)
        event_timestamps['source'], event_values['source'] = res

        # compare event times and values between methods
        np.testing.assert_array_equal(event_timestamps['index'], event_timestamps['name'])
        np.testing.assert_array_equal(event_timestamps['index'], event_timestamps['source'])

        np.testing.assert_array_equal(event_values['index'], event_values['name'])
        np.testing.assert_array_equal(event_values['index'], event_values['name'])


def test_compare_FileReader_analog_data(reader):

    for i in range(reader.pl2_file_info.m_TotalNumberOfAnalogChannels):
        # loading channel info via index, name and source methods
        channel_info = reader.pl2_get_analog_channel_info(i)
        channel_name = channel_info.m_Name
        source_id = channel_info.m_Source
        channel_id_in_source = channel_info.m_Channel
        n_frag = channel_info.m_MaximumNumberOfFragments

        # set up arguments for running analog data methods
        fragment_timestamps = {}
        fragment_counts = {}
        values = {}

        # Check if channel is an integer or string, and call appropriate function
        res = reader.pl2_get_analog_channel_data(i)
        fragment_timestamps['index'], fragment_counts['index'], values['index'] = res

        res = reader.pl2_get_analog_channel_data_by_name(channel_name)
        fragment_timestamps['name'], fragment_counts['name'], values['name'] = res

        reader.pl2_get_analog_channel_data_by_source(source_id, channel_id_in_source)
        fragment_timestamps['source'], fragment_counts['source'], values['source'] = res

        # compare times, counts and value arrays between methods
        np.testing.assert_array_equal(fragment_timestamps['index'], fragment_timestamps['name'])
        np.testing.assert_array_equal(fragment_timestamps['index'], fragment_timestamps['source'])

        np.testing.assert_array_equal(fragment_counts['index'], fragment_counts['name'])
        np.testing.assert_array_equal(fragment_counts['index'], fragment_counts['name'])

        np.testing.assert_array_equal(values['index'], values['name'])
        np.testing.assert_array_equal(values['index'], values['name'])

