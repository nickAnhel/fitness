from __future__ import annotations

import calendar
import uuid
from collections import defaultdict
from datetime import datetime, date, timedelta

from src.profile import schemas
from src.profile.repository import ProfileRepository


class ProfileService:
    def __init__(self, repository: ProfileRepository) -> None:
        self.repository = repository

    async def get_profile(
        self,
        status_id: uuid.UUID | None = None,
        month: date | None = None,
        page: int = 1,
        per_page: int = 5,
    ) -> dict[str, object] | None:
        user = await self.repository.get_first_user()
        if not user:
            return None

        statuses = await self.repository.list_statuses()
        total_subs = await self.repository.count_subscriptions(user.user_id, status_id=status_id)
        safe_page, safe_per_page, offset = self._normalize_pagination(page, per_page)
        subs = await self.repository.list_subscriptions_paginated(
            user.user_id, status_id=status_id, limit=safe_per_page, offset=offset
        )
        visits = await self.repository.list_visits(user.user_id, month=month)

        calendar_days, current_month, prev_month, next_month, month_label = self._build_calendar(visits, month)

        return {
            "user": schemas.User.model_validate(user),
            "statuses": [schemas.SubscriptionStatus.model_validate(s) for s in statuses],
            "selected_status_id": status_id,
            "subscriptions": [self._map_subscription(s) for s in subs],
            "subscription_pagination": self._pagination_meta(total_subs, safe_page, safe_per_page),
            "visits": [self._map_visit(v) for v in visits],
            "calendar_days": calendar_days,
            "current_month": current_month,
            "prev_month": prev_month,
            "next_month": next_month,
            "month_label": month_label,
        }

    def _map_subscription(self, subscription) -> schemas.Subscription:
        base = schemas.Subscription.model_validate(subscription)
        return base.model_copy(
            update={
                "status": schemas.SubscriptionStatus.model_validate(subscription.status),
                "branch_name": subscription.branch.name,
                "tariff_name": subscription.tariff.name,
                "price": getattr(subscription.tariff, "price", None),
            }
        )

    def _map_visit(self, visit) -> schemas.Visit:
        base = schemas.Visit.model_validate(visit)
        return base.model_copy(
            update={
                "branch_name": visit.branch.name,
            },
        )

    def _normalize_pagination(self, page: int, per_page: int) -> tuple[int, int, int]:
        safe_page = max(page, 1)
        safe_per_page = max(per_page, 1)
        return safe_page, safe_per_page, (safe_page - 1) * safe_per_page

    def _pagination_meta(self, total: int, page: int, per_page: int) -> dict[str, int | bool]:
        safe_per_page = max(per_page, 1)
        pages = (total + safe_per_page - 1) // safe_per_page if safe_per_page else 1
        current = min(page, pages) if pages else 1
        return {
            "total": total,
            "page": current,
            "per_page": safe_per_page,
            "pages": max(pages, 1),
            "has_prev": current > 1,
            "has_next": current < max(pages, 1),
            "prev_page": current - 1,
            "next_page": current + 1,
        }

    def _build_calendar(self, visits, month: date | None) -> tuple[list[dict], date, str, str, str]:
        today = datetime.utcnow().date()
        base_date = month or (max((v.entered_at.date() for v in visits), default=today))
        first_day = base_date.replace(day=1)
        _, days_in_month = calendar.monthrange(first_day.year, first_day.month)

        visit_map: defaultdict[str, int] = defaultdict(int)
        for v in visits:
            day_key = v.entered_at.date().isoformat()
            visit_map[day_key] += 1

        days: list[dict] = []
        for day in range(1, days_in_month + 1):
            current_date = first_day.replace(day=day)
            key = current_date.isoformat()
            days.append(
                {
                    "date": key,
                    "day": day,
                    "visits": visit_map.get(key, 0),
                    "is_today": current_date == today,
                }
            )
        prev_month_date = (first_day - timedelta(days=1)).replace(day=1)
        next_month_date = (first_day + timedelta(days=32)).replace(day=1)
        month_label = self._month_label(first_day)
        return days, first_day, prev_month_date.strftime("%Y-%m"), next_month_date.strftime("%Y-%m"), month_label

    def _month_label(self, current: date) -> str:
        names = [
            "январь",
            "февраль",
            "март",
            "апрель",
            "май",
            "июнь",
            "июль",
            "август",
            "сентябрь",
            "октябрь",
            "ноябрь",
            "декабрь",
        ]
        return f"{names[current.month - 1].capitalize()} {current.year}"
