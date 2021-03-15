import time
import numpy as np
import threading

from pylsl import StreamInlet, resolve_stream, LostError, resolve_byprop, StreamInfo, StreamOutlet, local_clock
import config
import pickle

# ref: https://stackoverflow.com/questions/21204206/faster-way-to-simultaneously-iterate-over-rolling-window-of-two-or-more-numpy-ar
def rolling_window(a, window):
    shape = a.shape[:-1] + (a.shape[-1] - window + 1, window)
    strides = a.strides + (a.strides[-1],)
    return np.lib.stride_tricks.as_strided(a, shape=shape, strides=strides)


class DEAPReader:

    def __init__(self):
        self._running = True
        self.sample_no = 0

    def terminate(self):
        self._running = False

    def run(self, deap_data, outlet):
        while self._running:
            if self.sample_no>deap_data.shape[1]-1:
                self.sample_no = 0
            subset = deap_data[:, self.sample_no]
            stamp = local_clock() - 0.125
            outlet.push_sample(subset.tolist(), stamp)
            self.sample_no += 1
            time.sleep(0.01)

class SimulationInterface:

    def __init__(self, lsl_data_type, num_channels, sampling_rate):  # default board_id 2 for Cyton
        self.lsl_data_type = lsl_data_type
        self.lsl_num_channels = num_channels
        with open('data/s01.dat', "rb") as f:
            deap_data = pickle.load(f, encoding="latin1")
        deap_data = np.array(deap_data['data'])
        # flatten so we have a continuous stream
        self.deap_data = deap_data.reshape(deap_data.shape[1],deap_data.shape[0]*deap_data.shape[2])
        self.dreader = None
        self.stream_process = None
        info = StreamInfo('DEAP Simulation', 'EEG', num_channels, sampling_rate, 'float32', 'deapcontinuous')
        self.outlet = StreamOutlet(info, 32, 360)
        self.streams = resolve_byprop('name', self.lsl_data_type, timeout=1)
        if len(self.streams) < 1:
            raise AttributeError('Unable to find LSL Stream with given type {0}'.format(lsl_data_type))
        self.inlet = StreamInlet(self.streams[0])
        pass

    def start_sensor(self):
        # connect to the sensor
        self.dreader = DEAPReader()
        self.stream_process = threading.Thread(target=self.dreader.run, args=(self.deap_data,self.outlet))

        self.stream_process.start()
        self.streams = resolve_byprop('name', self.lsl_data_type, timeout=1)
        if len(self.streams) < 1:
            raise AttributeError('Unable to find LSL Stream with given type {0}'.format(self.lsl_data_type))
        self.inlet = StreamInlet(self.streams[0])
        self.inlet.open_stream()
        print('LSLInletInterface: resolved, created and opened inlet for lsl stream with type ' + self.lsl_data_type)

        # read the channel names is there's any
        # tell the sensor to start sending frames

    def process_frames(self):
        # return one or more frames of the sensor
        try:
            frames, timestamps = self.inlet.pull_chunk()
        except LostError:
            frames, timestamps = [], []
            pass  # TODO handle stream lost
        return np.transpose(frames), timestamps

    def stop_sensor(self):
        self.dreader.terminate()
        if self.inlet:
            self.inlet.close_stream()
        print('LSLInletInterface: inlet stream closed.')

    def info(self):
        return self.inlet.info()


def run_test():
    data = np.empty(shape=(config.UNITY_LSL_CHANNEL_SIZE, 0))
    print('Started streaming')
    start_time = time.time()
    while 1:
        try:
            new_data, _ = unityLSL_inferface.process_frames()
            print(new_data)
            if len(new_data) > 0:
                data = np.concatenate((data, new_data), axis=-1)  # get all data and remove it from internal buffer
        except KeyboardInterrupt:
            f_sample = data.shape[-1] / (time.time() - start_time)
            print('Stopped streaming, sampling rate = ' + str(f_sample))
            break
    return data


if __name__ == "__main__":
    unityLSL_inferface = LSLInletInterface()
    unityLSL_inferface.start_sensor()
    data = run_test()
    unityLSL_inferface.stop_sensor()