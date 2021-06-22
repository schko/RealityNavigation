import time
import numpy as np

from pylsl import StreamInlet, resolve_stream

import config


# class UnityLSLInterface:
#
#     def __init__(self, lsl_data_type='Unity.EyeData'):  # default board_id 2 for Cyton
#         self.lsl_data_type = lsl_data_type
#         self.streams = None
#         self.inlet = None
#         pass
#
#     def start_sensor(self):
#         # connect to the sensor
#         self.streams = resolve_stream('type', self.lsl_data_type)
#         self.inlet = StreamInlet(self.streams[0])
#         self.inlet.open_stream()
#         print('UnityLSLInterface: resolved, created and opened inlet for lsl stream with type ' + self.lsl_data_type)
#         # tell the sensor to start sending frames
#
#     def process_frames(self):
#         # return one or more frames of the sensor
#         frames, timestamps = self.inlet.pull_chunk()
#         return np.transpose(frames), timestamps
#
#     def stop_sensor(self):
#         self.inlet.close_stream()
#         print('UnityLSLInterface: inlet stream closed.')
#
#     def info(self):
#         return self.inlet.info()


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
    unityLSL_inferface = UnityLSLInterface()
    unityLSL_inferface.start_sensor()
    data = run_test()
    unityLSL_inferface.stop_sensor()
