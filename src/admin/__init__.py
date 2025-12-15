from pathlib import Path

from fastapi import FastAPI
from sqladmin import Admin, ModelView
from sqladmin.authentication import AuthenticationBackend
from sqladmin.filters import ForeignKeyFilter
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.orm.exc import DetachedInstanceError
from starlette.requests import Request
from wtforms.validators import DataRequired

from src.auth.models import SessionModel
from src.branches.models import BranchModel, DiscountTypeModel, DistrictModel
from src.common.database import async_engine, async_session_maker
from src.common.security import hash_password
from src.config import settings
from src.employees.models import EmployeeModel, EmployeeRoleModel, RoleModel
from src.promotions.models import PromotionModel
from src.notifications.service import notify_new_promotion, notify_subscription_created, notify_subscription_status_change
from src.subscriptions.models import SubscriptionModel, SubscriptionStatusModel
from src.tariffs.models import TariffModel, TariffTypeModel, TariffValidityPeriodModel
from src.users.models import UserModel
from src.visits.models import VisitModel


TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"


def _render_relations(rel) -> str:
    """Render many-to-many relations; return an em dash if unavailable."""
    try:
        items = list(rel or [])
    except DetachedInstanceError:
        return "—"
    except Exception:
        return "—"
    return ", ".join(str(item) for item in items) or "—"


class BaseAdminView(ModelView):
    page_size = 50
    column_display_pk = False

    async def is_accessible(self, request: Request) -> bool:  # type: ignore[override]
        roles = set(request.session.get("roles", []))
        return ADMIN_ROLE in roles


class DistrictAdmin(BaseAdminView, model=DistrictModel):
    name = "Район"
    name_plural = "Районы"
    category = "Сеть"
    column_list = [DistrictModel.name]
    column_searchable_list = [DistrictModel.name]
    column_sortable_list = [DistrictModel.name]
    column_details_exclude_list = [DistrictModel.district_id, DistrictModel.branches]
    form_excluded_columns = [DistrictModel.district_id, DistrictModel.branches]
    column_labels = {
        DistrictModel.name.key: "Название",
    }


class BranchAdmin(BaseAdminView, model=BranchModel):
    name = "Филиал"
    name_plural = "Филиалы"
    category = "Сеть"
    column_list = [
        BranchModel.name,
        BranchModel.address,
        BranchModel.is_active,
        BranchModel.district,
    ]
    column_details_list = [
        BranchModel.name,
        BranchModel.address,
        BranchModel.is_active,
        BranchModel.district,
        BranchModel.employees,
        BranchModel.promotions,
    ]
    column_searchable_list = [BranchModel.name, BranchModel.address]
    column_sortable_list = [BranchModel.name, BranchModel.is_active]
    column_labels = {
        BranchModel.name.key: "Название",
        BranchModel.address.key: "Адрес",
        BranchModel.is_active.key: "Активен",
        BranchModel.district.key: "Район",
        BranchModel.description.key: "Описание",
        BranchModel.contacts.key: "Контакты",
        BranchModel.operating_hours.key: "Часы работы",
        BranchModel.employees: "Сотрудники",
        BranchModel.promotions: "Акции",
    }
    column_default_sort = (BranchModel.name, False)
    form_excluded_columns = [
        BranchModel.employees,
        BranchModel.subscriptions,
        BranchModel.visits,
        BranchModel.promotions,
        BranchModel.branch_id,
    ]
    column_filters = [
        ForeignKeyFilter(
            BranchModel.district_id,
            DistrictModel.name,
            foreign_model=DistrictModel,
            title="Район",
        )
    ]
    def list_query(self, request):
        return (
            select(BranchModel)
            .options(
                selectinload(BranchModel.employees),
                selectinload(BranchModel.promotions),
                selectinload(BranchModel.district),
            )
        )

    def details_query(self, request):
        return (
            self._stmt_by_identifier(request.path_params["pk"])
            .options(
                selectinload(BranchModel.employees),
                selectinload(BranchModel.promotions),
                selectinload(BranchModel.district),
            )
        )


class DiscountTypeAdmin(BaseAdminView, model=DiscountTypeModel):
    name = "Тип скидки"
    name_plural = "Типы скидок"
    category = "Продажи"
    column_list = [DiscountTypeModel.name]
    column_searchable_list = [DiscountTypeModel.name]
    column_details_exclude_list = [DiscountTypeModel.discount_type_id, DiscountTypeModel.promotions]
    form_excluded_columns = [DiscountTypeModel.discount_type_id, DiscountTypeModel.promotions]
    column_labels = {
        DiscountTypeModel.name.key: "Название",
    }


class TariffTypeAdmin(BaseAdminView, model=TariffTypeModel):
    name = "Тип тарифа"
    name_plural = "Типы тарифов"
    category = "Тарифы"
    column_list = [TariffTypeModel.name]
    column_searchable_list = [TariffTypeModel.name]
    column_details_exclude_list = [TariffTypeModel.tariff_type_id, TariffTypeModel.tariffs]
    form_excluded_columns = [TariffTypeModel.tariff_type_id, TariffTypeModel.tariffs]
    column_labels = {
        TariffTypeModel.name.key: "Название",
    }


class TariffValidityPeriodAdmin(BaseAdminView, model=TariffValidityPeriodModel):
    name = "Срок действия"
    name_plural = "Сроки действия тарифа"
    category = "Тарифы"
    column_list = [TariffValidityPeriodModel.duration_days]
    column_sortable_list = [TariffValidityPeriodModel.duration_days]
    column_details_exclude_list = [
        TariffValidityPeriodModel.tariff_validity_period_id,
        TariffValidityPeriodModel.tariffs,
    ]
    form_excluded_columns = [TariffValidityPeriodModel.tariff_validity_period_id, TariffValidityPeriodModel.tariffs]
    column_labels = {
        TariffValidityPeriodModel.duration_days.key: "Длительность (дней)",
    }


class TariffAdmin(BaseAdminView, model=TariffModel):
    name = "Тариф"
    name_plural = "Тарифы"
    category = "Тарифы"
    can_create = True
    can_edit = True
    column_list = [
        TariffModel.name,
        TariffModel.price,
        TariffModel.is_available,
        TariffModel.tariff_type,
        TariffModel.validity_period,
    ]
    column_details_list = [
        TariffModel.name,
        TariffModel.price,
        TariffModel.is_available,
        TariffModel.tariff_type,
        TariffModel.validity_period,
        TariffModel.description,
        TariffModel.promotions,

    ]
    column_searchable_list = [TariffModel.name]
    column_sortable_list = [TariffModel.price, TariffModel.is_available]
    column_labels = {
        TariffModel.name.key: "Название",
        TariffModel.price.key: "Цена",
        TariffModel.is_available.key: "Доступен",
        TariffModel.tariff_type.key: "Тип тарифа",
        TariffModel.validity_period.key: "Срок действия",
        TariffModel.description.key: "Описание",
        TariffModel.promotions: "Акции",
    }
    column_default_sort = (TariffModel.price, False)
    form_excluded_columns = [
        TariffModel.promotions,
        TariffModel.subscriptions,
        TariffModel.tariff_id,
    ]
    column_filters = [
        ForeignKeyFilter(
            TariffModel.tariff_validity_period_id,
            TariffValidityPeriodModel.duration_days,
            foreign_model=TariffValidityPeriodModel,
            title="Срок действия",
        ),
        ForeignKeyFilter(
            TariffModel.tariff_type_id,
            TariffTypeModel.name,
            foreign_model=TariffTypeModel,
            title="Тип тарифа",
        ),
    ]

    def list_query(self, request):
        return select(TariffModel).options(
            selectinload(TariffModel.tariff_type),
            selectinload(TariffModel.validity_period),
            selectinload(TariffModel.promotions),
        )

    def details_query(self, request):
        return self._stmt_by_identifier(request.path_params["pk"]).options(
            selectinload(TariffModel.tariff_type),
            selectinload(TariffModel.validity_period),
            selectinload(TariffModel.promotions),
        )


class PromotionAdmin(BaseAdminView, model=PromotionModel):
    name = "Акция"
    name_plural = "Акции"
    category = "Акции"
    can_delete = True
    column_list = [
        PromotionModel.name,
        PromotionModel.starts_at,
        PromotionModel.ends_at,
        PromotionModel.discount_value,
        PromotionModel.is_active,
        PromotionModel.discount_type,
    ]
    column_details_list = [
        PromotionModel.name,
        PromotionModel.starts_at,
        PromotionModel.ends_at,
        PromotionModel.discount_value,
        PromotionModel.is_active,
        PromotionModel.discount_type,
        PromotionModel.branches,
        PromotionModel.tariffs,
    ]
    column_searchable_list = [PromotionModel.name]
    column_sortable_list = [PromotionModel.starts_at, PromotionModel.ends_at]
    column_labels = {
        PromotionModel.name.key: "Название",
        PromotionModel.starts_at.key: "Начало",
        PromotionModel.ends_at.key: "Окончание",
        PromotionModel.discount_value.key: "Размер скидки",
        PromotionModel.is_active.key: "Активна",
        PromotionModel.discount_type.key: "Тип скидки",
        PromotionModel.description.key: "Описание",
        PromotionModel.usage_limit.key: "Лимит использований",
        PromotionModel.branches: "Филиалы",
        PromotionModel.tariffs: "Тарифы",
    }
    form_excluded_columns = [
        PromotionModel.promotion_branches,
        PromotionModel.promotion_tariffs,
        PromotionModel.promotion_id,
    ]
    column_filters = [
        ForeignKeyFilter(
            PromotionModel.discount_type_id,
            DiscountTypeModel.name,
            foreign_model=DiscountTypeModel,
            title="Тип скидки",
        )
    ]
    def list_query(self, request):
        return select(PromotionModel).options(
            selectinload(PromotionModel.branches),
            selectinload(PromotionModel.tariffs),
            selectinload(PromotionModel.discount_type),
        )

    def details_query(self, request):
        return self._stmt_by_identifier(request.path_params["pk"]).options(
            selectinload(PromotionModel.branches),
            selectinload(PromotionModel.tariffs),
            selectinload(PromotionModel.discount_type),
        )

    async def insert_model(self, request, data):  # type: ignore[override]
        promotion = await super().insert_model(request, data)
        if promotion:
            await notify_new_promotion(promotion.promotion_id)
        return promotion


class SubscriptionStatusAdmin(BaseAdminView, model=SubscriptionStatusModel):
    name = "Статус"
    name_plural = "Статусы абонементов"
    category = "Абонементы"
    column_list = [SubscriptionStatusModel.name]
    column_searchable_list = [SubscriptionStatusModel.name]
    column_details_exclude_list = [SubscriptionStatusModel.subscription_status_id, SubscriptionStatusModel.subscriptions]
    form_excluded_columns = [
        SubscriptionStatusModel.subscription_status_id,
        SubscriptionStatusModel.subscriptions,
    ]
    column_labels = {
        SubscriptionStatusModel.name.key: "Название",
    }


class SubscriptionAdmin(BaseAdminView, model=SubscriptionModel):
    name = "Абонемент"
    name_plural = "Абонементы"
    category = "Абонементы"
    can_delete = False
    column_list = [
        SubscriptionModel.user,
        SubscriptionModel.branch,
        SubscriptionModel.tariff,
        SubscriptionModel.status,
        SubscriptionModel.start_date,
    ]
    column_details_list = [
        SubscriptionModel.user,
        SubscriptionModel.branch,
        SubscriptionModel.tariff,
        SubscriptionModel.status,
        SubscriptionModel.start_date,
    ]
    column_sortable_list = [SubscriptionModel.start_date]
    column_default_sort = (SubscriptionModel.start_date, True)
    column_filters = [
        ForeignKeyFilter(
            SubscriptionModel.subscription_status_id,
            SubscriptionStatusModel.name,
            foreign_model=SubscriptionStatusModel,
            title="Статус",
        )
    ]
    column_labels = {
        SubscriptionModel.user.key: "Пользователь",
        SubscriptionModel.branch.key: "Филиал",
        SubscriptionModel.tariff.key: "Тариф",
        SubscriptionModel.status.key: "Статус",
        SubscriptionModel.start_date.key: "Дата начала",
    }
    form_excluded_columns = [
        SubscriptionModel.subscription_id,
        SubscriptionModel.user_id,
        SubscriptionModel.branch_id,
        SubscriptionModel.tariff_id,
        SubscriptionModel.subscription_status_id,
    ]

    def list_query(self, request):
        return select(SubscriptionModel).options(
            selectinload(SubscriptionModel.user).selectinload(UserModel.visits),
            selectinload(SubscriptionModel.branch),
            selectinload(SubscriptionModel.tariff),
            selectinload(SubscriptionModel.status),
            selectinload(SubscriptionModel.user).selectinload(UserModel.subscriptions),
        )

    def details_query(self, request):
        return self._stmt_by_identifier(request.path_params["pk"]).options(
            selectinload(SubscriptionModel.user).selectinload(UserModel.visits),
            selectinload(SubscriptionModel.user).selectinload(UserModel.subscriptions),
            selectinload(SubscriptionModel.branch),
            selectinload(SubscriptionModel.tariff),
            selectinload(SubscriptionModel.status),
        )
    async def is_accessible(self, request: Request) -> bool:  # type: ignore[override]
        roles = set(request.session.get("roles", []))
        return ADMIN_ROLE in roles or LOCAL_ADMIN_ROLE in roles

    async def insert_model(self, request, data):  # type: ignore[override]
        subscription = await super().insert_model(request, data)
        if subscription:
            await notify_subscription_created(subscription.subscription_id)
        return subscription

    async def update_model(self, request, pk, data):  # type: ignore[override]
        previous_status = None
        async with async_session_maker() as session:
            stmt = select(SubscriptionModel.subscription_status_id).where(SubscriptionModel.subscription_id == pk)
            result = await session.execute(stmt)
            previous_status = result.scalar_one_or_none()

        subscription = await super().update_model(request, pk, data)
        if subscription and subscription.subscription_status_id != previous_status:
            await notify_subscription_status_change(subscription.subscription_id)
        return subscription


class VisitAdmin(BaseAdminView, model=VisitModel):
    name = "Посещение"
    name_plural = "Посещения"
    category = "Посещения"
    column_list = [
        VisitModel.user,
        VisitModel.branch,
        VisitModel.entered_at,
        VisitModel.exited_at,
    ]
    column_details_exclude_list = [VisitModel.visit_id, VisitModel.user_id, VisitModel.branch_id]
    column_sortable_list = [VisitModel.entered_at]
    column_default_sort = (VisitModel.entered_at, True)
    column_labels = {
        VisitModel.user.key: "Пользователь",
        VisitModel.branch.key: "Филиал",
        VisitModel.entered_at.key: "Время входа",
        VisitModel.exited_at.key: "Время выхода",
    }


class SessionAdmin(BaseAdminView, model=SessionModel):
    name = "Сессия"
    name_plural = "Сессии"
    category = "Сессии"
    can_create = False
    column_details_list = [
        UserModel.first_name,
        UserModel.last_name,
        UserModel.middle_name,
        UserModel.birth_date,
        UserModel.email,
        UserModel.phone,
        UserModel.login,
        UserModel.registered_at,
        UserModel.is_blocked,
        "subscriptions_display",
        "visits_display",
    ]
    can_edit = False
    can_delete = False
    can_view_details = False
    column_list = [
        SessionModel.user,
        SessionModel.created_at,
        SessionModel.expires_at,
    ]
    column_sortable_list = [SessionModel.created_at, SessionModel.expires_at]
    column_default_sort = (SessionModel.created_at, True)
    column_labels = {
        SessionModel.user.key: "Пользователь",
        SessionModel.created_at.key: "Создана",
        SessionModel.expires_at.key: "Истекает",
    }


ADMIN_ROLE = "Администратор"
LOCAL_ADMIN_ROLE = "Локальный администратор"


class AdminAuth(AuthenticationBackend):
    async def login(self, request: Request) -> bool:
        form = await request.form()
        login = (form.get("username") or "").strip()
        password = form.get("password") or ""
        if not login or not password:
            return False

        async with async_session_maker() as session:
            stmt = select(EmployeeModel).where(EmployeeModel.login == login)
            result = await session.execute(stmt)
            employee = result.scalars().first()

        if not employee or not employee.password_hash:
            return False

        if employee.password_hash != hash_password(password):
            return False

        async with async_session_maker() as session:
            roles_stmt = (
                select(RoleModel.name)
                .join(EmployeeRoleModel, EmployeeRoleModel.role_id == RoleModel.role_id)
                .where(EmployeeRoleModel.employee_id == employee.employee_id)
            )
            roles_result = await session.execute(roles_stmt)
            role_names = [row[0] for row in roles_result.all()]

        request.session["employee_id"] = str(employee.employee_id)
        request.session["roles"] = role_names
        return bool(role_names)

    async def logout(self, request: Request) -> bool:
        request.session.clear()
        return True

    async def authenticate(self, request: Request) -> bool:
        return bool(request.session.get("employee_id"))


class UserAdmin(BaseAdminView, model=UserModel):
    name = "Пользователь"
    name_plural = "Пользователи"
    category = "Пользователи"
    can_create = False
    column_details_list = [
        UserModel.first_name,
        UserModel.last_name,
        UserModel.middle_name,
        UserModel.birth_date,
        UserModel.email,
        UserModel.phone,
        UserModel.login,
        UserModel.registered_at,
        UserModel.is_blocked,
        UserModel.subscriptions,
        UserModel.visits,
    ]
    column_list = [
        UserModel.first_name,
        UserModel.last_name,
        UserModel.middle_name,
        UserModel.birth_date,
        UserModel.email,
        UserModel.phone,
        UserModel.login,
        UserModel.registered_at,
        UserModel.is_blocked,
    ]
    column_searchable_list = [
        UserModel.first_name,
        UserModel.last_name,
        UserModel.email,
        UserModel.phone,
        UserModel.login,
    ]
    column_sortable_list = [UserModel.registered_at, UserModel.is_blocked]
    column_labels = {
        UserModel.first_name.key: "Имя",
        UserModel.last_name.key: "Фамилия",
        UserModel.middle_name.key: "Отчество",
        UserModel.birth_date.key: "Дата рождения",
        UserModel.email.key: "Электронная почта",
        UserModel.phone.key: "Телефон",
        UserModel.login.key: "Логин",
        UserModel.registered_at.key: "Дата регистрации",
        UserModel.is_blocked.key: "Заблокирован",
        UserModel.subscriptions: "Абонементы",
        UserModel.visits: "Посещения",
    }
    column_default_sort = (UserModel.registered_at, True)
    form_excluded_columns = [
        UserModel.password_hash,
        UserModel.subscriptions,
        UserModel.visits,
        UserModel.user_id,
    ]

    def list_query(self, request):
        return (
            select(UserModel)
            .options(
                selectinload(UserModel.subscriptions).selectinload(SubscriptionModel.branch),
                selectinload(UserModel.subscriptions).selectinload(SubscriptionModel.tariff),
                selectinload(UserModel.subscriptions).selectinload(SubscriptionModel.status),
                selectinload(UserModel.visits).selectinload(VisitModel.branch),
            )
        )

    def details_query(self, request):
        return (
            self._stmt_by_identifier(request.path_params["pk"])
            .options(
                selectinload(UserModel.subscriptions).selectinload(SubscriptionModel.branch),
                selectinload(UserModel.subscriptions).selectinload(SubscriptionModel.tariff),
                selectinload(UserModel.subscriptions).selectinload(SubscriptionModel.status),
                selectinload(UserModel.visits).selectinload(VisitModel.branch),
            )
        )

    async def is_accessible(self, request: Request) -> bool:  # type: ignore[override]
        roles = set(request.session.get("roles", []))
        return ADMIN_ROLE in roles or LOCAL_ADMIN_ROLE in roles


class RoleAdmin(BaseAdminView, model=RoleModel):
    name = "Роль"
    name_plural = "Роли"
    category = "Персонал"
    column_list = [RoleModel.name, RoleModel.description]
    column_searchable_list = [RoleModel.name]
    column_details_exclude_list = [RoleModel.role_id, RoleModel.employee_roles]
    column_labels = {
        RoleModel.name.key: "Название",
        RoleModel.description.key: "Описание",
    }
    form_excluded_columns = [RoleModel.employee_roles, RoleModel.role_id]


class EmployeeRoleAdmin(BaseAdminView, model=EmployeeRoleModel):
    name = "Назначение"
    name_plural = "Назначения"
    category = "Персонал"
    can_create = True
    can_edit = True
    column_list = [
        EmployeeRoleModel.employee,
        EmployeeRoleModel.role,
    ]
    column_details_exclude_list = [
        EmployeeRoleModel.employee_role_id,
        EmployeeRoleModel.employee_id,
        EmployeeRoleModel.role_id,
    ]
    column_searchable_list = []
    column_labels = {
        EmployeeRoleModel.employee.key: "Сотрудник",
        EmployeeRoleModel.role.key: "Роль",
    }
    form_excluded_columns = [
        EmployeeRoleModel.employee_role_id,
        EmployeeRoleModel.employee_id,
        EmployeeRoleModel.role_id,
    ]
    async def is_accessible(self, request: Request) -> bool:  # type: ignore[override]
        roles = set(request.session.get("roles", []))
        return ADMIN_ROLE in roles


class EmployeeAdmin(BaseAdminView, model=EmployeeModel):
    name = "Сотрудник"
    name_plural = "Сотрудники"
    category = "Персонал"
    column_list = [
        EmployeeModel.first_name,
        EmployeeModel.last_name,
        EmployeeModel.email,
        EmployeeModel.phone,
        EmployeeModel.employment_date,
        EmployeeModel.employee_roles,
    ]
    column_details_list = [
        EmployeeModel.first_name,
        EmployeeModel.last_name,
        EmployeeModel.email,
        EmployeeModel.phone,
        EmployeeModel.employment_date,
        EmployeeModel.login,
        EmployeeModel.birth_date,
        EmployeeModel.employee_roles,
        EmployeeModel.branches,
    ]
    column_searchable_list = [
        EmployeeModel.first_name,
        EmployeeModel.last_name,
        EmployeeModel.email,
        EmployeeModel.phone,
    ]
    column_default_sort = (EmployeeModel.employment_date, True)
    form_excluded_columns = [
        EmployeeModel.employee_id,
    ]
    column_labels = {
        EmployeeModel.first_name.key: "Имя",
        EmployeeModel.last_name.key: "Фамилия",
        EmployeeModel.middle_name.key: "Отчество",
        EmployeeModel.birth_date.key: "Дата рождения",
        EmployeeModel.email.key: "Электронная почта",
        EmployeeModel.phone.key: "Телефон",
        EmployeeModel.employment_date.key: "Дата приема",
        EmployeeModel.login.key: "Логин",
        EmployeeModel.password_hash.key: "Пароль",
        EmployeeModel.employee_roles: "Должности",
    }  # type: ignore[arg-type]
    form_args = {
        EmployeeModel.password_hash.key: {  # type: ignore[arg-type]
            "label": "Пароль",
            "validators": [DataRequired()],
        }
    }
    form_create_rules = [
        "first_name",
        "last_name",
        "middle_name",
        "birth_date",
        "employment_date",
        "email",
        "phone",
        "login",
        "password_hash",
    ]
    def list_query(self, request):
        return select(EmployeeModel).options(
            selectinload(EmployeeModel.employee_roles).selectinload(EmployeeRoleModel.role),
            selectinload(EmployeeModel.branches),
        )

    def details_query(self, request):
        return self._stmt_by_identifier(request.path_params["pk"]).options(
            selectinload(EmployeeModel.employee_roles).selectinload(EmployeeRoleModel.role),
            selectinload(EmployeeModel.branches),
        )

    async def insert_model(self, request, data):  # type: ignore[override]
        password_value = data.pop("password_hash", None)
        if not password_value:
            raise ValueError("Пароль обязателен при создании сотрудника")
        data["password_hash"] = hash_password(password_value)
        return await super().insert_model(request, data)

    async def update_model(self, request, pk, data):  # type: ignore[override]
        password_value = data.pop("password_hash", None)
        if password_value:
            data["password_hash"] = hash_password(password_value)
        return await super().update_model(request, pk, data)


def setup_admin_panel(app: FastAPI) -> None:
    admin = Admin(
        app,
        engine=async_engine,
        title="Админка Fitness",
        templates_dir=str(TEMPLATES_DIR),
        authentication_backend=AdminAuth(settings.project.session_secret),
    )
    admin.add_view(UserAdmin)
    admin.add_view(BranchAdmin)
    admin.add_view(DistrictAdmin)
    admin.add_view(DiscountTypeAdmin)
    admin.add_view(TariffTypeAdmin)
    admin.add_view(TariffValidityPeriodAdmin)
    admin.add_view(TariffAdmin)
    admin.add_view(PromotionAdmin)
    admin.add_view(SubscriptionStatusAdmin)
    admin.add_view(SubscriptionAdmin)
    admin.add_view(VisitAdmin)
    admin.add_view(SessionAdmin)
    admin.add_view(RoleAdmin)
    admin.add_view(EmployeeRoleAdmin)
    admin.add_view(EmployeeAdmin)

    app.state.admin = admin
