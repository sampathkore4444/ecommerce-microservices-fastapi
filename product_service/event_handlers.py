from shared.message_queue import message_queue, MessageType
from sqlalchemy.orm import Session
import logging
from .models import Product

logger = logging.getLogger(__name__)


async def handle_order_created(message: dict, db: Session):
    """Handle order creation events - update inventory"""
    order_data = message["data"]

    for item in order_data["items"]:
        # Update product inventory
        product = db.query(Product).filter(Product.id == item["product_id"]).first()
        if product:
            product.stock -= item["quantity"]
            db.commit()
            logger.info(f"Updated inventory for product {product.id}")

            # Check if inventory is low
            if product.stock < 10:  # Threshold for low inventory
                await message_queue.publish_message(
                    MessageType.INVENTORY_LOW,
                    {"product_id": product.id, "stock": product.stock},
                )


async def handle_order_cancelled(message: dict, db: Session):
    """Handle order cancellation - restore inventory"""
    order_data = message["data"]

    for item in order_data["items"]:
        product = db.query(Product).filter(Product.id == item["product_id"]).first()
        if product:
            product.stock += item["quantity"]
            db.commit()
            logger.info(f"Restored inventory for product {product.id}")


async def publish_product_updated(product_data: dict):
    """Publish product update events"""
    await message_queue.publish_message(MessageType.PRODUCT_UPDATED, product_data)
