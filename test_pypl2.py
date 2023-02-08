import os.path
import sys
import subprocess
import difflib
import pathlib
import pytest

from pypl2api import pl2_ad, pl2_spikes, pl2_events, pl2_info
from pypl2lib import PyPL2FileReader, PL2FileInfo, PL2SpikeChannelInfo, PL2DigitalChannelInfo, PL2AnalogChannelInfo

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
    import zugbruecke
    assert not sys.platform.startswith(
        'win'), 'Test requires to run on a non-windows system to use zugbruecke'

    data_file_1 = 'dumped_example_data_using_zugbruecke.txt'
    dump_loaded_example_data(data_file_1)

    data_file_2 = 'dumped_example_data_using_wenv.txt'
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
def reader_and_file_info():
    # Get file infos
    filename = pathlib.Path(__file__).parent / 'data' / '4chDemoPL2.pl2'
    reader = PyPL2FileReader()
    reader.pl2_open_file(filename)

    file_info = PL2FileInfo()
    reader.pl2_get_file_info(file_info)
    return reader, file_info


def test_compare_FileReader_SpikeChannelInfo(reader_and_file_info):
    reader, file_info = reader_and_file_info

    for i in range(file_info.m_TotalNumberOfSpikeChannels):
        # loading channel info via index, name and source methods
        channel_info_by_index = PL2SpikeChannelInfo()
        channel_info_by_name = PL2SpikeChannelInfo()
        channel_info_by_source = PL2SpikeChannelInfo()

        reader.pl2_get_spike_channel_info(i, channel_info_by_index)
        channel_name = channel_info_by_index.m_Name
        source_id = channel_info_by_index.m_Source
        channel_id_in_source = channel_info_by_index.m_Channel

        reader.pl2_get_spike_channel_info_by_name(channel_name, channel_info_by_name)
        reader.pl2_get_spike_channel_info_by_source(source_id, channel_id_in_source, channel_info_by_source)

        # comparing results
        assert_object_fields_are_equal(channel_info_by_index, channel_info_by_name, channel_info_by_source)


def test_compare_FileReader_AnalogChannelInfo(reader_and_file_info):
    reader, file_info = reader_and_file_info

    for i in range(file_info.m_TotalNumberOfAnalogChannels):
        # loading channel info via index, name and source methods
        channel_info_by_index = PL2AnalogChannelInfo()
        channel_info_by_name = PL2AnalogChannelInfo()
        channel_info_by_source = PL2AnalogChannelInfo()

        reader.pl2_get_analog_channel_info(i, channel_info_by_index)
        channel_name = channel_info_by_index.m_Name
        source_id = channel_info_by_index.m_Source
        channel_id_in_source = channel_info_by_index.m_Channel

        reader.pl2_get_analog_channel_info_by_name(channel_name, channel_info_by_name)
        reader.pl2_get_analog_channel_info_by_source(source_id, channel_id_in_source, channel_info_by_source)

        # comparing results
        assert_object_fields_are_equal(channel_info_by_index, channel_info_by_name,
                                       channel_info_by_source)


def test_compare_FileReader_DigitalChannelInfo(reader_and_file_info):
    reader, file_info = reader_and_file_info

    for i in range(file_info.m_NumberOfDigitalChannels):
        # loading channel info via index, name and source methods
        channel_info_by_index = PL2DigitalChannelInfo()
        channel_info_by_name = PL2DigitalChannelInfo()
        channel_info_by_source = PL2DigitalChannelInfo()

        reader.pl2_get_digital_channel_info(i, channel_info_by_index)
        channel_name = channel_info_by_index.m_Name
        source_id = channel_info_by_index.m_Source
        channel_id_in_source = channel_info_by_index.m_Channel

        reader.pl2_get_digital_channel_info_by_name(channel_name, channel_info_by_name)
        reader.pl2_get_digital_channel_info_by_source(source_id, channel_id_in_source,
                                                     channel_info_by_source)

        # comparing results
        assert_object_fields_are_equal(channel_info_by_index, channel_info_by_name,
                                       channel_info_by_source)

    def test_compare_FileReader_DigitalChannelInfo(reader_and_file_info):
        reader, file_info = reader_and_file_info

        for i in range(file_info.m_NumberOfDigitalChannels):
            # loading channel info via index, name and source methods
            channel_info_by_index = PL2DigitalChannelInfo()
            channel_info_by_name = PL2DigitalChannelInfo()
            channel_info_by_source = PL2DigitalChannelInfo()

            reader.pl2_get_digital_channel_info(i, channel_info_by_index)
            channel_name = channel_info_by_index.m_Name
            source_id = channel_info_by_index.m_Source
            channel_id_in_source = channel_info_by_index.m_Channel

            reader.pl2_get_digital_channel_info_by_name(channel_name, channel_info_by_name)
            reader.pl2_get_digital_channel_info_by_source(source_id, channel_id_in_source,
                                                          channel_info_by_source)

            # comparing results
            assert_object_fields_are_equal(channel_info_by_index, channel_info_by_name,
                                           channel_info_by_source)

    # TODO: Also compare other methods:
    # reader.pl2_get_spike_channel_data()
    # reader.pl2_get_analog_channel_data()
    # reader.pl2_get_digital_channel_data()
