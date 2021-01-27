from utils.general import slice_len_for

REFRESH_INTERVAL = 4

OPENBCI_EEG_CHANNEL_SIZE = 31
OPENBCI_EEG_USEFUL_CHANNELS = slice(1, 17)
OPENBCI_EEG_SAMPLING_RATE = 125.
OPENBCI_EEG_USEFUL_CHANNELS_NUM = slice_len_for(OPENBCI_EEG_USEFUL_CHANNELS, OPENBCI_EEG_CHANNEL_SIZE)

UNITY_LSL_CHANNEL_SIZE = 17
UNITY_LSL_SAMPLING_RATE = 70.
UNITY_LSL_USEFUL_CHANNELS = slice(1, 10)
UNITY_LSL_USEFUL_CHANNELS_NUM = slice_len_for(UNITY_LSL_USEFUL_CHANNELS, UNITY_LSL_CHANNEL_SIZE)

PLOT_RETAIN_HISTORY = 10.  # retain 10 seconds of history
