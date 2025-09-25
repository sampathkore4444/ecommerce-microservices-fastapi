from shared.message_queue import message_queue, MessageType
import logging

logger = logging.getLogger(__name__)


async def publish_user_registered(user_data: dict):
    """Publish user registration events"""
    await message_queue.publish_message(MessageType.USER_REGISTERED, user_data)


async def handle_order_events(message: dict):
    """Handle order events to update user statistics"""
    order_data = message["data"]
    user_id = order_data["user_id"]

    # Update user order statistics
    logger.info(f"Updating statistics for user {user_id}")
    # Implementation would update user's order count, total spent, etc.
