# Kafka producer disabled for Render deployment (no Redpanda available)
# Kafka analytics is active in full local Docker setup

import os
import json
from aiokafka import AIOKafkaProducer

KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "redpanda:29092")

_producer: AIOKafkaProducer | None = None


async def start_kafka_producer() -> None:
    """
    Create and start the singleton AIOKafkaProducer.
    Called once at application startup via lifespan.
    One persistent TCP connection is reused for all sends.
    """
    global _producer
    _producer = AIOKafkaProducer(
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
    )
    await _producer.start()


async def stop_kafka_producer() -> None:
    """
    Flush buffered messages and close the Kafka connection.
    Called once at application shutdown via lifespan.
    """
    global _producer
    if _producer is not None:
        await _producer.stop()
        _producer = None


async def send_click_event(short_code: str) -> None:
    """
    Publish a click event to the 'clicks' topic.
    The analytics worker consumes this and increments click_count in the DB.
    Guard: if producer is unavailable, silently no-ops.
    Redirect latency is never affected by Kafka availability.
    """
    if _producer is None:
        return
    await _producer.send("clicks", {"short_code": short_code})


async def send_new_url_event(short_code: str, long_url: str) -> None:
    """
    Publish a new-URL event to the 'new_urls' topic.
    The classifier worker consumes this, runs zero-shot classification
    via HuggingFace, and writes the category back to the DB.
    Guard: if producer is unavailable, silently no-ops.
    """
    if _producer is None:
        return
    await _producer.send("new_urls", {"short_code": short_code, "long_url": long_url})
    
