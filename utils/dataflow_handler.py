import argparse
import datetime
import json
import logging

import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions
import apache_beam.transforms.window as window
import os

class GroupWindowsIntoBatches(beam.PTransform):
    """A composite transform that groups Pub/Sub messages based on publish
    time and outputs a list of dictionaries, where each contains one message
    and its publish timestamp.
    """

    def __init__(self, gap_size):
        # Convert seconds into float.
        self.gap_size = float(gap_size)

    def expand(self, pcoll):
        return (
            pcoll
            # Assigns window info to each Pub/Sub message based on its
            # publish timestamp.
            | "Window into Sessions"
            >> beam.WindowInto(window.Sessions(self.gap_size))
            | "Add timestamps to messages" >> beam.ParDo(AddTimestamps())
            # Use a dummy key to group the elements in the same window.
            # Note that all the elements in one window must fit into memory
            # for this. If the windowed elements do not fit into memory,
            # please consider using `beam.util.BatchElements`.
            # https://beam.apache.org/releases/pydoc/current/apache_beam.transforms.util.html#apache_beam.transforms.util.BatchElements
            | "Add Dummy Key" >> beam.Map(lambda elem: (None, elem))
            | "Groupby" >> beam.GroupByKey()
            | "Abandon Dummy Key" >> beam.MapTuple(lambda _, val: val)
        )


class AddTimestamps(beam.DoFn):
    def process(self, element, publish_time=beam.DoFn.TimestampParam):
        """Processes each incoming windowed element by extracting the Pub/Sub
        message and its publish timestamp into a dictionary. `publish_time`
        defaults to the publish timestamp returned by the Pub/Sub server. It
        is bound to each element by Beam at runtime.
        """

        yield {
            "message_body": element.decode("utf-8"),
            "publish_time": datetime.datetime.utcfromtimestamp(
                float(publish_time)
            ).strftime("%Y-%m-%d %H:%M:%S.%f"),
        }


class WriteBatchesToGCS(beam.DoFn):
    def __init__(self, output_path):
        self.output_path = output_path

    def process(self, batch, window=beam.DoFn.WindowParam):
        """Write one batch per file to a Google Cloud Storage bucket. """

        ts_format = "%Y-%m-%d %H:%M:%S.%f"
        window_start = window.start.to_utc_datetime().strftime(ts_format)
        window_end = window.end.to_utc_datetime().strftime(ts_format)
        filename = "-".join([self.output_path, window_start, window_end])

        with beam.io.gcp.gcsio.GcsIO().open(filename=filename, mode="w") as f:
            for element in batch:
                f.write("{}\n".format(json.dumps(element)).encode("utf-8"))


def run(input_topic, output_path, bucket, project, region, gap_size=0.5):
    # `save_main_session` is set to true because some DoFn's rely on
    # globally imported modules.
    pipeline_options = PipelineOptions(
        runner='DataflowRunner',temp_location="gs://"+bucket+"/temp", project=project, region=region, streaming=True, save_main_session=True
    )

    with beam.Pipeline(options=pipeline_options) as pipeline:
        (
            pipeline
            | "Read PubSub Messages"
            >> beam.io.ReadFromPubSub(topic=input_topic)
            | "Window into" >> GroupWindowsIntoBatches(gap_size)
            | "Write to GCS" >> beam.ParDo(WriteBatchesToGCS(output_path))
        )


if __name__ == "__main__":  # noqa
    logging.getLogger().setLevel(logging.INFO)

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--project",
        type=str,
        default='vae-cloud-model',
        help="Project name.",
    )
    parser.add_argument(
        "--bucket",
        type=str,
        default='raw-model-data',
        help="Storage bucket.",
    )
    parser.add_argument(
        "--region",
        type=str,
        default='us-central1',
        help="GCP Region.",
    )
    parser.add_argument(
        "--topic_id",
        type=str,
        default='test_topic',
        help="PubSub topic."
    )
    parser.add_argument(
        "--gap_size",
        type=float,
        default=0.5,
        help="Output file's window size in number of minutes.",
    )
    parser.add_argument(
        "--auth_path",
        type=str,
        default="C:/Users/LIINC/OneDrive/Documents/Sharath/RealityNavigation/auth/vae-cloud-model-cfe6512aaa99.json",
        help="Auth file path.",
    )
    known_args, pipeline_args = parser.parse_known_args()

    os.environ[
        "GOOGLE_APPLICATION_CREDENTIALS"] = known_args.auth_path

    input_topic = 'projects/' + known_args.project + '/topics/' + known_args.topic_id
    output_path = "gs://" + known_args.bucket + "/results/outputs"
    run(
        input_topic = input_topic,
        output_path = output_path,
        gap_size = known_args.gap_size,
        bucket = known_args.bucket,
        project = known_args.project,
        region = known_args.region
    )