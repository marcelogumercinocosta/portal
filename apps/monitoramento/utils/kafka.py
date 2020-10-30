import itertools
import json
import math

from django.conf import settings
from pykafka import KafkaClient, exceptions
from pykafka.common import OffsetType


class Kafka:
    def __init__(self, topic, last_lines):
        self.last_lines = last_lines
        self.client = KafkaClient(hosts=settings.KAFKA_SERVER)
        self.topic = self.client.topics[topic]
        self.consumer = self.topic.get_simple_consumer(auto_offset_reset=OffsetType.LATEST, reset_offset_on_start=True, consumer_timeout_ms=2000)
        
    def get_kafka_topic(self):
        result = []
        LAST_N_MESSAGES = self.last_lines
        MAX_PARTITION_REWIND = int(math.ceil(LAST_N_MESSAGES / len(self.consumer.partitions)))
        held_offsets = self.consumer.held_offsets[0] - MAX_PARTITION_REWIND
        offsets = [(self.consumer.partitions[0], (held_offsets if held_offsets > -1 else -2))]
        self.consumer.reset_offsets(offsets)
        for message in itertools.islice(self.consumer, LAST_N_MESSAGES):
            result.append(json.loads((message.value).decode()))
        return result

    def get_kafka_topic_last(self):
        LAST_N_MESSAGES = 1
        MAX_PARTITION_REWIND = int(math.ceil(LAST_N_MESSAGES / len(self.consumer.partitions)))
        held_offsets = self.consumer.held_offsets[0] - MAX_PARTITION_REWIND
        offsets = [(self.consumer.partitions[0], (held_offsets if held_offsets > -1 else -2))]
        self.consumer.reset_offsets(offsets)
        for message in itertools.islice(self.consumer, LAST_N_MESSAGES):
            result = message.offset

