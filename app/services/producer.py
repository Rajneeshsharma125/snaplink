# Kafka producer disabled for Render deployment (no Redpanda available)
# Kafka analytics is active in full local Docker setup

import os
import json
import asyncio
import logging
from aiokafka import AIOKafkaProducer

log = logging.getLogger(__name__)

KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "redpanda:29092")

_producer: AIOKafkaProducer | None = None


async def start_kafka_producer() -> None:
    """
    Create and start the singleton AIOKafkaProducer.
    Called once at application startup via lifespan.
    Retries 5 times with 5-second delays to tolerate slow Redpanda startup.
    If all retries fail (e.g. Render — no Kafka available), _producer stays
    None and all send functions silently no-op. App starts and serves traffic.
    """
    global _producer
    retries = 5
    delay = 5
    for attempt in range(retries):
        try:
            log.info("Connecting to Kafka (attempt %d/%d)...", attempt + 1, retries)
            producer = AIOKafkaProducer(
                bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
                value_serializer=lambda v: json.dumps(v).encode("utf-8"),
            )
            await producer.start()
            _producer = producer
            log.info("Kafka producer connected.")
            return
        except Exception as e:
            log.warning("Kafka connection attempt %d failed: %s", attempt + 1, e)
            if attempt < retries - 1:
                await asyncio.sleep(delay)
    log.error(
        "Kafka producer failed to connect after %d attempts. "
        "Analytics disabled — app will continue without it.",
        retries,
    )


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
    Guard: if producer is None (Kafka unavailable), silently no-ops.
    Redirect latency is never affected by Kafka availability.
    """
    if _producer is None:
        return
    try:
        await _producer.send("clicks", {"short_code": short_code})
    except Exception as e:
        log.warning("send_click_event failed for %s: %s", short_code, e)


async def send_new_url_event(short_code: str, long_url: str) -> None:
    """
    Publish a new-URL event to the 'new_urls' topic.
    The classifier worker consumes this, runs zero-shot classification
    via HuggingFace, and writes the category back to the DB.
    Guard: if producer is None (Kafka unavailable), silently no-ops.
    """
    if _producer is None:
        return
    try:
        await _producer.send("new_urls", {"short_code": short_code, "long_url": long_url})
    except Exception as e:
        log.warning("send_new_url_event failed for %s: %s", short_code, e)
