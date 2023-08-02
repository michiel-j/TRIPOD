from xml.etree import ElementTree as ET
import pandas as pd
import numpy as np


def read_grail_raw_xml_simple(input_file):
    """
    Read Grail (Motek Medical) raw data from the .mox file.

    Args:
        input_file (str): xml (.mox) input file name.

    Returns:
        (DataFrame): DataFrame with information.
    """
    # Parse the XML tree and get the root.
    xmltree = ET.parse(input_file)
    xmlroot = xmltree.getroot()

    # (nr_of_channels, nr_of_samples, subject_bodymass, subject_gender) = self.__extract_params_from_header(xmlroot)
    nr_of_samples= __get_nr_of_samples(xmlroot)

    # Get a list of all gait parameters to extract, based on the config made in the constructor.
    xmlparameters = __get_xmlparameters()

    # Copy the sampling rate of 'Walking.Speed'. NOTE: dirty solution! (TODO)
    # Define a time axis based on sampling rate 'fs'
    fs = int(xmlroot[1][104][1][0].text)
    time = np.linspace(0, nr_of_samples/fs, nr_of_samples)

    # Extract the configured gait parameters from the Grail .mox file.
    gait_params = __extract_params(xmlroot=xmlroot, xmlparameters=xmlparameters, fs=fs)

    # Add the time axis to the dictionary of gait parameters.
    gait_params['time'] = time

    # Sanity check to see if all gait parameters have equal length.
    for key in gait_params.keys():
        assert (nr_of_samples == len(gait_params[key])), 'ERROR: Not all \'raw_gait_params\' have equal length.'

    return pd.DataFrame(data=gait_params)






"""
Private functions
"""
def __get_nr_of_samples(xmlroot) -> int:
    """
    Function to get the number of samples from the XML headers.
    Input:
        - xmlroot: the XML root as given by ET library.
    Output:
        - nr_of_samples: the total number of samples in the (raw) time series.
    """
    # Extract interesting parameters out of 'viewer_header'.
    try:
        moxie_prefix = '{http://www.small.nl/vumc/rev/moxie}' # Sort of prefix in the XML file.
        # nr_of_channels = int(xmlroot[0].find(moxie_prefix + 'nr_of_channels').text)
        nr_of_samples = int(xmlroot[0].find(moxie_prefix + 'nr_of_samples').text)
        # subject_bodymass = float(xmlroot[0].find(moxie_prefix + 'subject_info').find(moxie_prefix + 'subject_bodymass').text)
        # subject_gender = xmlroot[0].find(moxie_prefix + 'subject_info').find(moxie_prefix + 'subject_gender').text
    except:
        moxie_prefix = '{http://www.smalll.nl/vumc/rev/moxie}' # Error in 'Healthy_003 mox file
        # nr_of_channels = int(xmlroot[0].find(moxie_prefix + 'nr_of_channels').text)
        nr_of_samples = int(xmlroot[0].find(moxie_prefix + 'nr_of_samples').text)
        # subject_bodymass = float(xmlroot[0].find(moxie_prefix + 'subject_info').find(moxie_prefix + 'subject_bodymass').text)
        # subject_gender = xmlroot[0].find(moxie_prefix + 'subject_info').find(moxie_prefix + 'subject_gender').text
    return nr_of_samples


def __get_xmlparameters() -> list:
    """
    Function to make a list of all gait parameters to be extracted out of Grail .mox file.
    """
    xmlparameters = []
    # Define left parameters
    xmlparameters.append('Belt.Speed')
    xmlparameters.append('Walking.Speed')
    xmlparameters.append('L.Step.Length')
    xmlparameters.append('L.Step.Width')
    xmlparameters.append('L.Stride.Time')
    xmlparameters.append('L.Stance.Time')
    xmlparameters.append('L.Swing.Time')

    # Copy left parameters (and adapt them) to get right ones
    for xmlparam in xmlparameters:
        # If 'xmlparam' is related to left side of body, copy this to right side
        if(xmlparam[:2] == 'L.'): xmlparameters.append( xmlparam.replace('L.', 'R.') )

    return xmlparameters


def __extract_params(xmlroot, xmlparameters, fs) -> dict:
    """
    Function to extract the configured gait parameters out of the provided XML.
    Input:
        - xmlroot: the XML file.
        - xmlparameters:
        - fs: sampling rate
    Output:
        A dictionary containing the requested gait parameters. Each parameter represents a dictionary key.
    """
    def cast_string_to_numpy(input: str):
        elements = input.split(' ') # Split the elements. Currently they form one massive string, with values separated by white spaces.

        # Delete empty entries ('')
        for i in range(len(elements)):
            if(elements[i] == ''):
                del elements[i]
                i -= 1

        elements = [float(elem) for elem in elements] # Convert every element from string to np.float32
        elements = np.asarray(elements, dtype=np.float32)
        return elements


    # This method does the same as the above, but is less error-prone. This is because it avoids the indices.
    # TODO: problem with Healthy_003, iterator==54
    gait_params = {}
    for iterator in range(len(xmlroot[1])):
        if(xmlroot[1][iterator][0].text in xmlparameters):
            key = xmlroot[1][iterator][0].text
            try: val = xmlroot[1][iterator][1][1].text
            except IndexError: val = xmlroot[1][iterator][2][1].text # To fix formatting issue of 'Healthy_003'
            val = cast_string_to_numpy(val) # Cast massive string to numpy vector of floats
            gait_params[key] = val

            # Also check gait parameter's (at iterator index) sampling rate to provided argument 'fs'
            try: assert (fs == int(xmlroot[1][iterator][1][0].text)), 'ERROR: Sampling rates do not match.'
            except IndexError:  assert (fs == int(xmlroot[1][iterator][2][0].text)), 'ERROR: Sampling rates do not match.' # To fix formatting issue of 'Healthy_003'
    return gait_params
