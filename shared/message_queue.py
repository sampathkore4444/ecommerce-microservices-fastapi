import aio_pika
import json
import os
from typing import Dict, Any, Callable
import logging
from enum import Enum

logger = logging.getLogger(__name__)


class MessageType(str, Enum):
    ORDER_CREATED = "order.created"
    ORDER_UPDATED = "order.updated"
    ORDER_CANCELLED = "order.cancelled"
    USER_REGISTERED = "user.registered"
    PRODUCT_UPDATED = "product.updated"
    INVENTORY_LOW = "inventory.low"


class MessageQueue:
    def __init__(self):
        self.connection = None
        self.channel = None
        self.rabbitmq_url = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost/")

    async def connect(self):
        """Establish connection to RabbitMQ"""
        try:
            self.connection = await aio_pika.connect_robust(self.rabbitmq_url)
            self.channel = await self.connection.channel()
            logger.info("Connected to RabbitMQ")
        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ: {e}")
            raise

    async def publish_message(self, message_type: MessageType, data: Dict[str, Any]):
        """Publish a message to the message queue"""
        if not self.connection:
            await self.connect()

        message_body = json.dumps(
            {
                "type": message_type,
                "data": data,
                "timestamp": str(os.getenv("TIMESTAMP", "")),
            }
        )

        await self.channel.default_exchange.publish(
            aio_pika.Message(
                body=message_body.encode(),
                content_type="application/json",
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
            ),
            routing_key=message_type.value,
        )
        logger.info(f"Published message: {message_type}")

    async def consume_messages(self, message_type: MessageType, callback: Callable):
        """Consume messages from a specific queue"""
        if not self.connection:
            await self.connect()

        queue = await self.channel.declare_queue(message_type.value, durable=True)

        async with queue.iterator() as queue_iter:
            async for message in queue_iter:
                async with message.process():
                    try:
                        body = json.loads(message.body.decode())
                        await callback(body)
                        logger.info(f"Processed message: {message_type}")
                    except Exception as e:
                        logger.error(f"Error processing message: {e}")

    async def close(self):
        """Close the connection"""
        if self.connection:
            await self.connection.close()
            logger.info("RabbitMQ connection closed")


# Global message queue instance
message_queue = MessageQueue()
