# pypl2api.py - High level functions for accessing
# .pl2 files. Mimics Plexon's Matlab PL2 SDK
#
# (c) 2016 Plexon, Inc., Dallas, Texas
# www.plexon.com
#
# This software is provided as-is, without any warranty.
# You are free to modify or share this file, provided that the above
# copyright notice is kept intact.

from collections import namedtuple

import numpy as np

from pypl2lib import *


def print_error(pypl2_file_reader_instance):
    error_message = (ctypes.c_char * 256)()
    pypl2_file_reader_instance.pl2_get_last_error(error_message, 256)
    print(error_message.value)


def to_array(c_array):
    return np.ctypeslib.as_array(c_array)


def to_array_nonzero(c_array):
    a = np.ctypeslib.as_array(c_array)
    return a[np.where(a)]


def pl2_ad(filename, channel):
    """
    Reads continuous data from specific file and channel.
    
    Usage:
        >>>adfrequency, n, timestamps, fragmentcounts, ad = pl2_ad(filename, channel)
        >>>res = pl2_ad(filename, channel)
    
    Args:
        filename - full path and filename of .pl2 file
        channel - zero-based channel index, or channel name
    
    Returns (named tuple fields):
        adfrequency - digitization frequency for the channel
        n - total number of data points
        timestamps - tuple of fragment timestamps (one timestamp per fragment, in seconds)
        fragmentcounts - tuple of fragment counts
        ad - tuple of raw a/d values in volts
        
        The returned data is in a named tuple object, so it can be accessed as a normal tuple: 
            >>>res = pl2_ad('data/file.pl2', 0)
            >>>res[0]
            40000
        or as a named tuple:
            >>>res.adfrequency
            40000
    
        If any error is detected, an error message is printed and the function returns 0
    """

    # Create an instance of PyPL2FileReader.
    p = PyPL2FileReader()

    # Open the file.
    p.pl2_open_file(filename)
    p.pl2_get_file_info()

    # Check if channel is an integer or string, and call appropriate function
    if type(channel) is int:
        achannel_info = p.pl2_get_analog_channel_info(channel)
    if type(channel) in (str, bytes):
        achannel_info = p.pl2_get_analog_channel_info_by_name(channel)

    # Set up instances of ctypes classes needed by pl2_get_analog_channel_data().
    # These will be filled in by the function.
    num_fragments_returned = ctypes.c_ulonglong(achannel_info.m_MaximumNumberOfFragments)
    num_data_points_returned = ctypes.c_ulonglong(achannel_info.m_NumberOfValues)
    fragment_timestamps = (ctypes.c_longlong * achannel_info.m_MaximumNumberOfFragments)()
    fragment_counts = (ctypes.c_ulonglong * achannel_info.m_MaximumNumberOfFragments)()
    values = (ctypes.c_short * achannel_info.m_NumberOfValues)()

    # Check if channel is an integer or string, and call appropriate function
    if type(channel) is int:
        res = p.pl2_get_analog_channel_data(channel,
                                            num_fragments_returned,
                                            num_data_points_returned,
                                            fragment_timestamps,
                                            fragment_counts,
                                            values)
    if type(channel) in (str, bytes):
        res = p.pl2_get_analog_channel_data_by_name(channel,
                                                    num_fragments_returned,
                                                    num_data_points_returned,
                                                    fragment_timestamps,
                                                    fragment_counts,
                                                    values)

    assert achannel_info.m_MaximumNumberOfFragments >= num_fragments_returned.value
    assert achannel_info.m_NumberOfValues >= num_data_points_returned.value

    # Close the file
    p.pl2_close_file()

    # Create a named tuple called PL2Ad.
    PL2Ad = namedtuple('PL2Ad', 'adfrequency n timestamps fragmentcounts ad')

    # Fill in and return named tuple.
    return PL2Ad(achannel_info.m_SamplesPerSecond,
                 num_data_points_returned.value,
                 to_array_nonzero(fragment_timestamps) / p.pl2_file_info.m_TimestampFrequency,
                 to_array_nonzero(fragment_counts),
                 to_array(values) * achannel_info.m_CoeffToConvertToUnits)


def pl2_spikes(filename, channel, unit=[]):
    """
    Reads spike data from a specific file and channel.
    
    Usage:
        >>>n, timestamps, units, waveforms = pl2_spikes(filename, channel)
        >>>res = pl2_spikes(filename, channel)
    
    Args:
        filename - full path and filename of .pl2 file
        channel - zero-based channel index, or channel name
    
    Returns (named tuple fields):
        n - number of spike waveforms
        timestamps - tuple of spike waveform timestamps in seconds
        units - tuple of spike waveform unit assignments (0 = unsorted, 1 = Unit A, 2 = Unit B, etc)
        waveforms - tuple of tuples with raw waveform a/d values in volts
        
        The returned data is in a named tuple object, so it can be accessed as a normal tuple: 
            >>>res = pl2_spikes('data/file.pl2', 0)
            >>>res[0]
            6589
        or as a named tuple:
            >>>res.n
            6589
        
        To access individual waveform values, address res.waveforms with the index of the waveform.
        Result shortened for example:
            >>>res.waveforms[49]
            (0.000345643, 0.000546342, ... , -0.03320040)
    
        If any error is detected, an error message is printed and the function returns 0
    """

    # Create an instance of PyPL2FileReader.
    p = PyPL2FileReader()

    # Verify that the file passed exists first.
    # Open the file.
    p.pl2_open_file(filename)

    # Create instance of PL2SpikeChannelInfo.
    schannel_info = PL2SpikeChannelInfo()

    # Check if channel is an integer or string, and call appropriate function
    if type(channel) is int:
        schannel_info = p.pl2_get_spike_channel_info(channel)
    if type(channel) in (str, bytes):
        schannel_info = p.pl2_get_spike_channel_info_by_name(channel)

    # Set up instances of ctypes classes needed by pl2_get_spike_channel_data().
    # These will be filled in by the function.
    num_spikes_returned = ctypes.c_ulonglong(schannel_info.m_NumberOfSpikes)
    spike_timestamps = (ctypes.c_ulonglong * schannel_info.m_NumberOfSpikes)()
    units = (ctypes.c_ushort * schannel_info.m_NumberOfSpikes)()
    values = (ctypes.c_short * (
                schannel_info.m_NumberOfSpikes * schannel_info.m_SamplesPerSpike))()

    if type(channel) is int:
        res = p.pl2_get_spike_channel_data(channel,
                                           num_spikes_returned,
                                           spike_timestamps,
                                           units,
                                           values)
    if type(channel) in (str, bytes):
        res = p.pl2_get_spike_channel_data_by_name(channel,
                                                   num_spikes_returned,
                                                   spike_timestamps,
                                                   units,
                                                   values)

    assert schannel_info.m_NumberOfSpikes == num_spikes_returned.value

    # Close the file
    p.pl2_close_file()

    # The c_short() array called 'values' is currently a one-dimensional array of
    # waveform samples, which isn't in volts, and it's not easy to just get one
    # waveform out of it. I want this to be converted to volts, and also be
    # converted to a tuple of tuples that contain the waveform voltage values.

    # Then, extract the waveforms from 'values' into a multi-dimensional
    # Python tuple. If there is a more 'Pythonic' way to do this, I want
    # to know about it!
    waveforms = (to_array(values) * schannel_info.m_CoeffToConvertToUnits).reshape(
        (num_spikes_returned.value, schannel_info.m_SamplesPerSpike))

    # Create a named tuple called PL2Spikes
    PL2Spikes = namedtuple('PL2Spikes', 'n timestamps units waveforms')

    return PL2Spikes(num_spikes_returned.value,
                     to_array(spike_timestamps) / p.pl2_file_info.m_TimestampFrequency,
                     to_array(units),
                     waveforms)


def pl2_events(filename, channel):
    """
    Reads event channel data from a specific file and event channel
    
    Usage:
        >>>n, timestamps, values = pl2_events(filename, channel)
        >>>res = pl2_events(filename, channel)
    Args:
        filename - full path of the file
        channel - 1-based event channel index, or event channel name;
        
    Returns (named tuple fields):
        n - number of events
        timestamps - array of timestamps (in seconds)
        values - array of event values (when event is a strobed word)
        
    The returned data is in a named tuple object, so it can be accessed as a normal tuple:
        >>>res = pl2_events('data/file.pl2', 1)
        >>>res[0]
        784
    or as a named tuple:
        >>>res.n
        784
    """

    # Create an instance of PyPL2FileReader.
    p = PyPL2FileReader()

    # Verify that the file passed exists first.
    # Open the file.
    p.pl2_open_file(filename)
    p.pl2_get_file_info()

    # Check if channel is an integer or string, and call appropriate function
    if type(channel) is int:
        echannel_info = p.pl2_get_digital_channel_info(channel)
    if type(channel) in (str, bytes):
        echannel_info = p.pl2_get_digital_channel_info_by_name(channel)

    # Set up instances of ctypes classes needed by pl2_get_digital_channel_data().
    # These will be filled in by the function.
    num_events_returned = ctypes.c_ulonglong(echannel_info.m_NumberOfEvents)
    event_timestamps = (ctypes.c_longlong * echannel_info.m_NumberOfEvents)()
    event_values = (ctypes.c_ushort * echannel_info.m_NumberOfEvents)()

    if type(channel) is int:
        res = p.pl2_get_digital_channel_data(channel,
                                             num_events_returned,
                                             event_timestamps,
                                             event_values)
    if type(channel) in (str, bytes):
        res = p.pl2_get_digital_channel_data_by_name(channel,
                                                     num_events_returned,
                                                     event_timestamps,
                                                     event_values)

    assert echannel_info.m_NumberOfEvents == num_events_returned.value

    # Close the file
    p.pl2_close_file()

    # Create a named tuple called PL2DigitalEvents
    PL2DigitalEvents = namedtuple('PL2DigitalEvents', 'n timestamps values')

    return PL2DigitalEvents(num_events_returned.value,
                            to_array(event_timestamps) / p.pl2_file_info.m_TimestampFrequency,
                            to_array(event_values))


def pl2_info(filename):
    """
    Reads a PL2 file and returns information about the file.
    
    Usage:
        >>>spkcounts, evtcounts, adcounts = pl2_info(filename)
        >>>res = pl2_info(filename)
    
    Args:
        filename - Full path of the file
    
    Returns (named tuple fields):
        spikes - tuple the length of enabled spike channels with tuples
                 consisting of the spike channel number, name, and tuple of 
                 unit counts. The returned named tuple fields are:
                    channel - channel number
                    name - channel name
                    units - tuple with number of waveforms assigned to units
                            0 (unsorted) through 255
        events - tuple the length of event channels that contain data with tuples
                 consisting of the event channel number, name, and number of events.
                 The returned named tuple fields are:
                    channel - channel number
                    name - channel name
                    n - number of events in the channel
        ad - tuple the length of enabled ad channels with tuples consisting of the ad
             channel number, name, and number of samples. The returned named tuple fields
             are:
                channel - channels name
                name - channel name
                n - number of samples in the channel
             
    The returned data is in a named tuple object, and it's filled with more named tuple objects.
    There are several ways to access returned data.
        >>>spikecounts, eventcounts, adcounts = pl2_info('data/file.pl2')
        >>>len(spikecounts)
        >>>4
        
    pl2_info returns a named tuple object, but in the above example the three elements have been
    unpacked already into tuples called spikecounts, eventcounts, and adcounts. The length of
    these tuples indicate how many channels were enabled, or had values in them in the case of 
    event channels (since events are always enabled).
        >>>spikecounts[2].name
        >>>'SPK03'
        
    Continuing the example, the third element returned in spikecounts (2 is the third element
    because tuple indexing starts from 0) has a field called name, which contains the channel's
    name, SPK03. Because you can treat named tuples like normal tuples, you could also get that 
    information by the index (because you read the documentation and know that the name field is
    the second element of the tuple).
        >>>spikecounts[2][1]
        >>>'SPK03'
        
    If you don't unpack the returned tuple, it's still easy to get the information. The unpacked
    named tuple has the fields spikes, events, and ad.
        >>>res = pl2_info('data/file.pl2')
        >>>res.spikes[2].name
        >>>'SPK03'
    """

    # Create an instance of PyPL2FileReader.
    p = PyPL2FileReader()

    # Verify that the file passed exists first.
    # Open the file.
    p.pl2_open_file(filename)
    p.pl2_get_file_info()

    # Lists that will be filled with tuples
    spike_counts = []
    event_counts = []
    ad_counts = []

    # Named tuples that will be appended into lists
    spike_info = namedtuple('spike_info', 'channel name units')
    event_info = namedtuple('event_info', 'channel name n')
    ad_info = namedtuple('ad_info', 'channel name n')

    # Get channel numbers, names, and unit counts for all enabled spike channels
    for i in range(p.pl2_file_info.m_TotalNumberOfSpikeChannels):
        schannel_info = p.pl2_get_spike_channel_info(i)

        if schannel_info.m_ChannelEnabled:
            spike_counts.append(spike_info(schannel_info.m_Channel, schannel_info.m_Name.decode('ascii'),
                                           tuple(schannel_info.m_UnitCounts)))

    # Get channel numbers, names, and counts for all event channels with data
    for i in range(p.pl2_file_info.m_NumberOfDigitalChannels):
        echannel_info = p.pl2_get_digital_channel_info(i)

        if echannel_info.m_NumberOfEvents:
            event_counts.append(event_info(echannel_info.m_Channel, echannel_info.m_Name.decode('ascii'),
                                           echannel_info.m_NumberOfEvents))

    # Get channel numbers, names, and counts for all enabled spike channels
    for i in range(p.pl2_file_info.m_TotalNumberOfAnalogChannels):
        achannel_info = p.pl2_get_analog_channel_info(i)

        if achannel_info.m_ChannelEnabled:
            ad_counts.append(ad_info(achannel_info.m_Channel, achannel_info.m_Name.decode('ascii'),
                                     achannel_info.m_NumberOfValues))

    # Close the file
    p.pl2_close_file()

    PL2Info = namedtuple('PL2Info', 'spikes events ad')

    return PL2Info(tuple(spike_counts), tuple(event_counts), tuple(ad_counts))
