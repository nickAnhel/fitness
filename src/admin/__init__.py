from fastapi import FastAPI
from sqladmin import Admin, ModelView
from sqladmin.authentication import AuthenticationBackend
from sqladmin.filters import ForeignKeyFilter
from sqlalchemy import select
from starlette.requests import Request
from wtforms.validators import DataRequired

from src.auth.models import SessionModel
from src.branches.models import BranchModel, DiscountTypeModel, DistrictModel
from src.common.database import async_engine, async_session_maker
from src.common.security import hash_password
from src.config import settings
from src.employees.models import EmployeeModel, EmployeeRoleModel, RoleModel
from src.promotions.models import PromotionModel
from src.subscriptions.models import SubscriptionModel, SubscriptionStatusModel
from src.tariffs.models import TariffModel, TariffTypeModel, TariffValidityPeriodModel
from src.users.models import UserModel
from src.visits.models import VisitModel


class BaseAdminView(ModelView):
    page_size = 50
    column_display_pk = True

    async def is_accessible(self, request: Request) -> bool:  # type: ignore[override]
        roles = set(request.session.get("roles", []))
        return ADMIN_ROLE in roles


class DistrictAdmin(BaseAdminView, model=DistrictModel):
    name_plural = "Районы"
    category = "Сеть"
    column_list = [DistrictModel.district_id, DistrictModel.name]
    column_searchable_list = [DistrictModel.name]
    column_sortable_list = [DistrictModel.name]


class BranchAdmin(BaseAdminView, model=BranchModel):
    name_plural = "Филиалы"
    category = "Сеть"
    column_list = [
        BranchModel.branch_id,
        BranchModel.name,
        BranchModel.address,
        BranchModel.is_active,
        BranchModel.district,
    ]
    column_searchable_list = [BranchModel.name, BranchModel.address]
    column_sortable_list = [BranchModel.name, BranchModel.is_active]
    column_labels = {"is_active": "Active"}
    column_default_sort = (BranchModel.name, False)
    form_excluded_columns = [
        BranchModel.employees,
        BranchModel.subscriptions,
        BranchModel.visits,
        BranchModel.promotions,
    ]
    column_filters = [
        ForeignKeyFilter(
            BranchModel.district_id,
            DistrictModel.name,
            foreign_model=DistrictModel,
            title="District",
        )
    ]


class DiscountTypeAdmin(BaseAdminView, model=DiscountTypeModel):
    name_plural = "Типы скидок"
    category = "Продажы"
    column_list = [DiscountTypeModel.discount_type_id, DiscountTypeModel.name]
    column_searchable_list = [DiscountTypeModel.name]


class TariffTypeAdmin(BaseAdminView, model=TariffTypeModel):
    name_plural = "Типы тарифов"
    category = "Тарифы"
    column_list = [TariffTypeModel.tariff_type_id, TariffTypeModel.name]
    column_searchable_list = [TariffTypeModel.name]


class TariffValidityPeriodAdmin(BaseAdminView, model=TariffValidityPeriodModel):
    name_plural = "Сроки действия тарифа"
    category = "Тарифы"
    column_list = [TariffValidityPeriodModel.tariff_validity_period_id, TariffValidityPeriodModel.duration_days]
    column_sortable_list = [TariffValidityPeriodModel.duration_days]


class TariffAdmin(BaseAdminView, model=TariffModel):
    name_plural = "Тарифы"
    category = "Тарифы"
    can_create = True
    can_edit = True
    column_list = [
        TariffModel.tariff_id,
        TariffModel.name,
        TariffModel.price,
        TariffModel.is_available,
        TariffModel.tariff_type,
        TariffModel.validity_period,
    ]
    column_searchable_list = [TariffModel.name]
    column_sortable_list = [TariffModel.price, TariffModel.is_available]
    column_labels = {"is_available": "Available"}
    column_default_sort = (TariffModel.price, False)
    form_excluded_columns = [TariffModel.promotions, TariffModel.subscriptions]
    column_filters = [
        ForeignKeyFilter(
            TariffModel.tariff_validity_period_id,
            TariffValidityPeriodModel.duration_days,
            foreign_model=TariffValidityPeriodModel,
            title="Validity period",
        ),
        ForeignKeyFilter(
            TariffModel.tariff_type_id,
            TariffTypeModel.name,
            foreign_model=TariffTypeModel,
            title="Tariff type",
        ),
    ]


class PromotionAdmin(BaseAdminView, model=PromotionModel):
    name_plural = "Акции"
    category = "Акции"
    column_list = [
        PromotionModel.promotion_id,
        PromotionModel.name,
        PromotionModel.starts_at,
        PromotionModel.ends_at,
        PromotionModel.discount_value,
        PromotionModel.is_active,
        PromotionModel.discount_type,
    ]
    column_searchable_list = [PromotionModel.name]
    column_sortable_list = [PromotionModel.starts_at, PromotionModel.ends_at]
    column_labels = {"is_active": "Active"}
    form_excluded_columns = [
        PromotionModel.branches,
        PromotionModel.tariffs,
        PromotionModel.promotion_branches,
        PromotionModel.promotion_tariffs,
    ]
    column_filters = [
        ForeignKeyFilter(
            PromotionModel.discount_type_id,
            DiscountTypeModel.name,
            foreign_model=DiscountTypeModel,
            title="Discount type",
        )
    ]


class SubscriptionStatusAdmin(BaseAdminView, model=SubscriptionStatusModel):
    name_plural = "Статусы абонементов"
    category = "Абонементы"
    column_list = [SubscriptionStatusModel.subscription_status_id, SubscriptionStatusModel.name]
    column_searchable_list = [SubscriptionStatusModel.name]


class SubscriptionAdmin(BaseAdminView, model=SubscriptionModel):
    name_plural = "Абонементы"
    category = "Абонементы"
    column_list = [
        SubscriptionModel.subscription_id,
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
            title="Status",
        )
    ]
    async def is_accessible(self, request: Request) -> bool:  # type: ignore[override]
        roles = set(request.session.get("roles", []))
        return ADMIN_ROLE in roles or LOCAL_ADMIN_ROLE in roles


class VisitAdmin(BaseAdminView, model=VisitModel):
    name_plural = "Посещения"
    category = "Посещения"
    column_list = [
        VisitModel.visit_id,
        VisitModel.user,
        VisitModel.branch,
        VisitModel.entered_at,
        VisitModel.exited_at,
    ]
    column_sortable_list = [VisitModel.entered_at]
    column_default_sort = (VisitModel.entered_at, True)


class SessionAdmin(BaseAdminView, model=SessionModel):
    name_plural = "Сессии"
    category = "Сессии"
    can_create = False
    can_edit = False
    column_list = [
        SessionModel.session_id,
        SessionModel.user,
        SessionModel.created_at,
        SessionModel.expires_at,
    ]
    column_sortable_list = [SessionModel.created_at, SessionModel.expires_at]
    column_default_sort = (SessionModel.created_at, True)


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
    name_plural = "Пользователи"
    category = "Пользователи"
    can_create = False
    column_list = [
        UserModel.user_id,
        UserModel.first_name,
        UserModel.last_name,
        UserModel.email,
        UserModel.phone,
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
    column_labels = {"is_blocked": "Blocked"}
    column_default_sort = (UserModel.registered_at, True)
    form_excluded_columns = [
        UserModel.password_hash,
        UserModel.subscriptions,
        UserModel.visits,
    ]

    async def is_accessible(self, request: Request) -> bool:  # type: ignore[override]
        roles = set(request.session.get("roles", []))
        return ADMIN_ROLE in roles or LOCAL_ADMIN_ROLE in roles


class RoleAdmin(BaseAdminView, model=RoleModel):
    name_plural = "Роли"
    category = "Персонал"
    column_list = [RoleModel.role_id, RoleModel.name, RoleModel.description]
    column_searchable_list = [RoleModel.name]
    form_excluded_columns = [RoleModel.employee_roles]


class EmployeeRoleAdmin(BaseAdminView, model=EmployeeRoleModel):
    name_plural = "Назначения"
    category = "Персонал"
    can_create = True
    can_edit = True
    column_list = [
        EmployeeRoleModel.employee_role_id,
        EmployeeRoleModel.employee,
        EmployeeRoleModel.role,
    ]
    column_searchable_list = []
    async def is_accessible(self, request: Request) -> bool:  # type: ignore[override]
        roles = set(request.session.get("roles", []))
        return ADMIN_ROLE in roles


class EmployeeAdmin(BaseAdminView, model=EmployeeModel):
    name_plural = "Сотрудники"
    category = "Персонал"
    column_list = [
        EmployeeModel.employee_id,
        EmployeeModel.first_name,
        EmployeeModel.last_name,
        EmployeeModel.email,
        EmployeeModel.phone,
        EmployeeModel.employment_date,
    ]
    column_searchable_list = [
        EmployeeModel.first_name,
        EmployeeModel.last_name,
        EmployeeModel.email,
        EmployeeModel.phone,
    ]
    column_default_sort = (EmployeeModel.employment_date, True)
    form_excluded_columns = [
        EmployeeModel.employee_roles,
        EmployeeModel.branches,
    ]
    column_labels = {EmployeeModel.password_hash.key: "Password"}  # type: ignore[arg-type]
    form_args = {
        EmployeeModel.password_hash.key: {  # type: ignore[arg-type]
            "label": "Password",
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
        title="Fitness Admin",
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
