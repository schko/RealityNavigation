from google.cloud import pubsub_v1
import json

import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions
import os

class DataFlow:

    def __init__(self, credentials = "auth/Sharath's Project-a05c51bd881f.json", project_id = 'serene-athlete-271523',
                 bucket = 'dataflow-eeg', region='us-central1'):
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.path.abspath(credentials)
        self.project_id = project_id
        self.topic_id = 'test_topic'
        self.subscription_id = 'test_topic-sub'
        self.timeout = 5.0
        self.BUCKET = bucket
        self.REGION = region
        self.count = 0
        self.output_path = "gs://"+self.BUCKET+"/results/outputs"
        self.pipeline_topic_id = 'projects/'+self.project_id+'/topics/'+self.topic_id


    def send_data(self, lsl_data_type,stream_data,timestamps):
        publisher = pubsub_v1.PublisherClient()
        # The `topic_path` method creates a fully qualified identifier
        # in the form `projects/{project_id}/topics/{topic_id}`
        topic_path = publisher.topic_path(self.project_id, self.topic_id)
        #if self.count < 10:
        data = "Message number " + str(self.count) + "; Data type " + lsl_data_type + ": " + \
               json.dumps(stream_data.tolist()) + '; Timestamps: ' + json.dumps(timestamps)
        self.count += 1
        # Data must be a bytestring
        data = data.encode("utf-8")
        # When you publish a message, the client returns a future.
        future = publisher.publish(topic_path, data)
