from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from src.common.database import async_session_maker
from src.notifications import publisher
from src.promotions.models import PromotionModel
from src.subscriptions.models import SubscriptionModel
from src.users.models import UserModel


async def _load_subscription(subscription_id: uuid.UUID) -> SubscriptionModel | None:
    async with async_session_maker() as session:
        stmt = (
            select(SubscriptionModel)
            .options(
                selectinload(SubscriptionModel.user),
                selectinload(SubscriptionModel.branch),
                selectinload(SubscriptionModel.tariff),
                selectinload(SubscriptionModel.status),
            )
            .where(SubscriptionModel.subscription_id == subscription_id)
        )
        result = await session.execute(stmt)
        return result.scalars().first()


async def notify_subscription_created(subscription_id: uuid.UUID) -> None:
    subscription = await _load_subscription(subscription_id)
    if not subscription or not subscription.user or not subscription.user.email:
        return

    publisher.notify_subscription_created(
        recipient=subscription.user.email,
        first_name=subscription.user.first_name,
        last_name=subscription.user.last_name,
        branch_name=subscription.branch.name,
        tariff_name=subscription.tariff.name,
        start_date=subscription.start_date,
    )


async def notify_subscription_status_change(subscription_id: uuid.UUID) -> None:
    subscription = await _load_subscription(subscription_id)
    if not subscription or not subscription.user or not subscription.user.email:
        return

    publisher.notify_subscription_status_change(
        recipient=subscription.user.email,
        first_name=subscription.user.first_name,
        last_name=subscription.user.last_name,
        status_name=subscription.status.name,
    )


async def notify_new_promotion(promotion_id: uuid.UUID) -> None:
    async with async_session_maker() as session:
        promo_stmt = (
            select(PromotionModel)
            .options(
                selectinload(PromotionModel.discount_type),
            )
            .where(PromotionModel.promotion_id == promotion_id)
        )
        promo_result = await session.execute(promo_stmt)
        promotion = promo_result.scalars().first()

        if not promotion:
            return

        users_result = await session.execute(
            select(UserModel.email, UserModel.first_name, UserModel.last_name)
            .where(UserModel.is_blocked.is_(False))
            .where(UserModel.email.is_not(None))
        )
        recipients = [(row[0], row[1], row[2]) for row in users_result.all() if row[0]]
        if not recipients:
            return

    discount_label = promotion.discount_type.name if promotion.discount_type else str(promotion.discount_value)
    publisher.notify_new_promotion(
        recipients=recipients,
        promotion_name=promotion.name,
        discount_label=discount_label,
        starts_at=promotion.starts_at,
        ends_at=promotion.ends_at,
    )
