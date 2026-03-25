# Kafka producer disabled for Render deployment (no Redpanda available)
# Kafka analytics is active in full local Docker setup

async def start_kafka_producer():
    pass

async def stop_kafka_producer():
    pass

async def send_click_event(short_code: str):
    pass

async def send_new_url_event(short_code: str, long_url: str):
    pass
