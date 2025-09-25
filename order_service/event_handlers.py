from shared.message_queue import message_queue, MessageType
from shared.schemas import OrderResponse
import logging

logger = logging.getLogger(__name__)


async def publish_order_events(order: OrderResponse, event_type: MessageType):
    """Publish order events to message queue"""
    try:
        await message_queue.publish_message(event_type, order.dict())
        logger.info(f"Published {event_type} event for order {order.id}")
    except Exception as e:
        logger.error(f"Failed to publish order event: {e}")


async def handle_inventory_updates(message: dict):
    """Handle inventory update responses from product service"""
    logger.info(f"Received inventory update: {message}")


# Order event publishing functions
async def publish_order_created(order: OrderResponse):
    await publish_order_events(order, MessageType.ORDER_CREATED)


async def publish_order_updated(order: OrderResponse):
    await publish_order_events(order, MessageType.ORDER_UPDATED)


async def publish_order_cancelled(order: OrderResponse):
    await publish_order_events(order, MessageType.ORDER_CANCELLED)
