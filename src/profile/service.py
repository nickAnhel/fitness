from __future__ import annotations

import calendar
import uuid
from collections import defaultdict
from datetime import date, datetime, timedelta

from src.branches import schemas as branch_schemas
from src.profile import schemas
from src.profile.repository import ProfileRepository
from src.tariffs import schemas as tariff_schemas


class ProfileService:
    def __init__(self, repository: ProfileRepository) -> None:
        self.repository = repository

    async def get_profile(
        self,
        user_id: uuid.UUID,
        status_id: uuid.UUID | None = None,
        month: date | None = None,
        branch_id: uuid.UUID | None = None,
        page: int = 1,
        per_page: int = 5,
    ) -> dict[str, object] | None:
        user = await self.repository.get_user(user_id)
        if not user:
            return None

        statuses = await self.repository.list_statuses()
        total_subs = await self.repository.count_subscriptions(user.user_id, status_id=status_id)
        safe_page, safe_per_page, offset = self._normalize_pagination(page, per_page)
        subs = await self.repository.list_subscriptions_paginated(
            user.user_id, status_id=status_id, limit=safe_per_page, offset=offset
        )
        visits = await self.repository.list_visits(user.user_id, month=month, branch_id=branch_id)
        branches = await self.repository.list_branches()
        tariffs = await self.repository.list_tariffs()
        default_status = await self.repository.get_default_status()

        calendar_days, current_month, prev_month, next_month, month_label = self._build_calendar(visits, month)
        visit_stats = self._visit_stats(visits)

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
            "branches": [branch_schemas.Branch.model_validate(b) for b in branches],
            "tariffs": [tariff_schemas.Tariff.model_validate(t) for t in tariffs],
            "default_status_id": default_status.subscription_status_id if default_status else None,
            "selected_branch_id": branch_id,
            "visit_stats": visit_stats,
        }

    async def update_profile(
        self,
        user_id: uuid.UUID,
        *,
        first_name: str,
        last_name: str,
        email: str,
        phone: str | None = None,
        middle_name: str | None = None,
    ) -> tuple[schemas.User | None, str | None]:
        if await self.repository.is_email_taken(email, exclude_user_id=user_id):
            return None, "Этот email уже используется"
        user = await self.repository.update_user_contacts(
            user_id=user_id,
            email=email,
            phone=phone,
            first_name=first_name,
            last_name=last_name,
            middle_name=middle_name,
        )
        if not user:
            return None, "Пользователь не найден"
        return schemas.User.model_validate(user), None

    async def create_subscription(
        self, user_id: uuid.UUID, *, branch_id: uuid.UUID, tariff_id: uuid.UUID, start_date: date
    ) -> tuple[schemas.Subscription | None, str | None]:
        status = await self.repository.get_default_status()
        if not status:
            return None, "Не найден базовый статус абонемента"
        branch = await self.repository.get_branch(branch_id)
        tariff = await self.repository.get_tariff(tariff_id)
        if not branch or not tariff:
            return None, "Выбранный филиал или тариф недоступен"

        subscription = await self.repository.create_subscription(
            user_id=user_id,
            branch_id=branch_id,
            tariff_id=tariff_id,
            status_id=status.subscription_status_id,
            start_date=start_date,
        )
        return self._map_subscription(subscription), None

    async def delete_visit(self, user_id: uuid.UUID, visit_id: uuid.UUID) -> bool:
        return await self.repository.delete_visit(user_id, visit_id)

    async def clear_visits(self, user_id: uuid.UUID) -> None:
        await self.repository.delete_all_visits(user_id)

    async def delete_account(self, user_id: uuid.UUID) -> None:
        await self.repository.delete_user_account(user_id)

    async def cancel_subscription(self, user_id: uuid.UUID, subscription_id: uuid.UUID) -> bool:
        cancel_status = await self.repository.get_status_by_name("Отменен")
        if not cancel_status:
            return False
        return await self.repository.set_subscription_status(
            user_id=user_id,
            subscription_id=subscription_id,
            status_id=cancel_status.subscription_status_id,
        )


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

    def _visit_stats(self, visits) -> dict[str, float | int]:
        total_visits = len(visits)
        total_seconds = 0
        for v in visits:
            if v.exited_at:
                total_seconds += max(0, int((v.exited_at - v.entered_at).total_seconds()))
        hours = round(total_seconds / 3600, 2)
        return {"total_visits": total_visits, "hours": hours}
