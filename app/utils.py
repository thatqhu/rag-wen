# app/utils.py

from kafka import KafkaProducer, KafkaConsumer
import json

KAFKA_BROKERS = 'localhost:9092'
DOC_TOPIC = 'doc_ingest_topic'

def get_producer():
    return KafkaProducer(
        bootstrap_servers=KAFKA_BROKERS,
        value_serializer=lambda v: json.dumps(v).encode('utf-8')
    )

def get_consumer():
    return KafkaConsumer(
        DOC_TOPIC,
        bootstrap_servers=KAFKA_BROKERS,
        auto_offset_reset='earliest',
        enable_auto_commit=True,
        group_id='doc_ingest_group',
        value_deserializer=lambda m: json.loads(m.decode('utf-8'))
    )
