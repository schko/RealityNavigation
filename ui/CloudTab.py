# This Python file uses the following encoding: utf-8
import os
from PyQt5 import QtWidgets, uic, sip

import numpy as np
from datetime import datetime

from utils.ui_utils import dialog_popup
from utils.pubsub_handler import DataFlow
import os
import subprocess

class CloudTab(QtWidgets.QWidget):
    def __init__(self, parent, lsl_data_buffer: dict):
        """
        :param lsl_data_buffer: dict, passed by reference. Do not modify, as modifying it makes a copy.
        :rtype: object
        """
        super().__init__()
        self.ui = uic.loadUi("ui/CloudTab.ui", self)

        self.recording_buffer = {}

        self.is_recording = False

        self.StartPipelineBtn.clicked.connect(self.start_pipeline_btn_pressed)
        self.StartRecordingBtn.clicked.connect(self.start_recording_btn_pressed)
        self.StopRecordingBtn.clicked.connect(self.stop_recording_btn_pressed)
        #self.StartRecordingBtn.setEnabled(False)
        self.StopRecordingBtn.setEnabled(False)
        self.parent = parent
        self.dataflow = None
        self.sentData = True
        self.stoppedTime = None
        self.stoppedRecording = False
        self.gap_size = 0.8 # how much to pause after each trial

    def kill(process):
        if process.poll() is None:  # still running
            process.kill()



    def start_pipeline_btn_pressed(self):
        project_id = self.project_id.toPlainText()
        region = self.region.toPlainText()
        bucket = self.bucket.toPlainText()
        if not self.dataflow:
            # start all programs
            processes = [subprocess.Popen(program, shell=True) for program in ['python utils/dataflow_handler.py '
                                                                               '--gap_size ' + str(self.gap_size) +
                                                                               ' --project ' + project_id +
                                                                               ' --region '+ region +
                                                                               ' --bucket ' + bucket +
                                                                               ' --auth_path ' + self.auth_file.toPlainText()
                                                                               ]]
        self.StartPipelineBtn.setEnabled(False)
        self.StartRecordingBtn.setEnabled(True)

        pass

    def start_recording_btn_pressed(self):
        if not self.dataflow:
            self.dataflow = DataFlow(credentials=self.auth_file.toPlainText(), project_id=self.project_id.toPlainText(),
                               bucket=self.bucket.toPlainText(), region=self.region.toPlainText())

        if len(self.parent.LSL_data_buffer_dicts.keys()) < 1:
            dialog_popup('You need at least one LSL stream opened to start recording!')
        self.recording_buffer = {}  # clear buffer
        self.is_recording = True

        self.StartRecordingBtn.setEnabled(False)
        self.StopRecordingBtn.setEnabled(True)

        pass

    def stop_recording_btn_pressed(self):
        self.is_recording = False
        self.stoppedRecording = True
        self.StopRecordingBtn.setEnabled(False)
        self.StartRecordingBtn.setEnabled(True)

    def update_buffers(self, data_dict: dict):
        if self.is_recording:
            if self.sentData:
                lsl_data_type = data_dict['lsl_data_type']  # what is the type of the newly-come data
                buffered_data = data_dict['frames']
                buffered_timestamps = data_dict['timestamps']
                self.dataflow.send_data(lsl_data_type=lsl_data_type, stream_data=buffered_data,
                                        timestamps=buffered_timestamps)
                if lsl_data_type=='Unity.TrialInfo' and self.sentData:
                    self.sentData = False
                    self.stoppedTime = datetime.now()
                pass
            elif not self.sentData:
                duration = datetime.now() - self.stoppedTime
                if duration.total_seconds() > self.gap_size:
                    self.sentData = True
        elif self.stoppedRecording:
            self.stoppedRecording = False