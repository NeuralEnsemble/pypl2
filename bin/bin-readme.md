These dlls are available as free download at:  
https://plexon.com/software-downloads/#software-downloads-SDKs

Under "OmniPlex and MAP Offline (For reading previously recorded data files)"
you can download the "OmniPlex and MAP Offline SDK Bundle".

The required files are in the bundle, at:

* Plexon Offline SDK
* Python PL2 Offline Files SDK.zip
* PyPL2
* bin

### October 2024 DLL Update
The DLLs have always supported the PL2_GetAnalogChannelDataSubset function, but this function was never exposed in the Python API until recently. There was a problem with the DLLs' implementation of the subset function that caused its performance to lag under certain conditions. The updated DLLs fix the problem.