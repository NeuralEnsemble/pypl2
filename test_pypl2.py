import os.path
import sys
import subprocess
import difflib
import pathlib

from pypl2api import pl2_ad, pl2_spikes, pl2_events, pl2_info


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


if __name__ == '__main__':
    if len(sys.argv) == 1:
        # run comparison test if no argument is provided
        test_compare_loading_wenv_zugbruecke()
    else:
        output_filename = sys.argv[1]
        dump_loaded_example_data(output_filename)
