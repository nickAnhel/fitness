"""add cascade deletes

Revision ID: 2f9f9d6a2c45
Revises: 9e7a6c3b55a1
Create Date: 2025-12-08 00:30:00.000000
"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "2f9f9d6a2c45"
down_revision: Union[str, None] = "9e7a6c3b55a1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # branches
    op.drop_constraint("branches_district_id_fkey", "branches", type_="foreignkey")
    op.create_foreign_key(
        "fk_branches_district_cascade", "branches", "districts", ["district_id"], ["district_id"], ondelete="CASCADE"
    )

    # tariffs
    op.drop_constraint("tariffs_tariff_type_id_fkey", "tariffs", type_="foreignkey")
    op.create_foreign_key(
        "fk_tariffs_tariff_type_cascade",
        "tariffs",
        "tariff_types",
        ["tariff_type_id"],
        ["tariff_type_id"],
        ondelete="CASCADE",
    )
    op.drop_constraint("tariffs_tariff_validity_period_id_fkey", "tariffs", type_="foreignkey")
    op.create_foreign_key(
        "fk_tariffs_validity_period_cascade",
        "tariffs",
        "tariff_validity_periods",
        ["tariff_validity_period_id"],
        ["tariff_validity_period_id"],
        ondelete="CASCADE",
    )

    # promotions
    op.drop_constraint("promotions_discount_type_id_fkey", "promotions", type_="foreignkey")
    op.create_foreign_key(
        "fk_promotions_discount_type_cascade",
        "promotions",
        "discount_types",
        ["discount_type_id"],
        ["discount_type_id"],
        ondelete="CASCADE",
    )

    # promotion junctions
    op.drop_constraint("promotion_branches_promotion_id_fkey", "promotion_branches", type_="foreignkey")
    op.create_foreign_key(
        "fk_promotion_branches_promotion_cascade",
        "promotion_branches",
        "promotions",
        ["promotion_id"],
        ["promotion_id"],
        ondelete="CASCADE",
    )
    op.drop_constraint("promotion_branches_branch_id_fkey", "promotion_branches", type_="foreignkey")
    op.create_foreign_key(
        "fk_promotion_branches_branch_cascade",
        "promotion_branches",
        "branches",
        ["branch_id"],
        ["branch_id"],
        ondelete="CASCADE",
    )
    op.drop_constraint("promotion_tariffs_promotion_id_fkey", "promotion_tariffs", type_="foreignkey")
    op.create_foreign_key(
        "fk_promotion_tariffs_promotion_cascade",
        "promotion_tariffs",
        "promotions",
        ["promotion_id"],
        ["promotion_id"],
        ondelete="CASCADE",
    )
    op.drop_constraint("promotion_tariffs_tariff_id_fkey", "promotion_tariffs", type_="foreignkey")
    op.create_foreign_key(
        "fk_promotion_tariffs_tariff_cascade",
        "promotion_tariffs",
        "tariffs",
        ["tariff_id"],
        ["tariff_id"],
        ondelete="CASCADE",
    )

    # subscriptions
    op.drop_constraint("subscriptions_user_id_fkey", "subscriptions", type_="foreignkey")
    op.create_foreign_key(
        "fk_subscriptions_user_cascade", "subscriptions", "users", ["user_id"], ["user_id"], ondelete="CASCADE"
    )
    op.drop_constraint("subscriptions_branch_id_fkey", "subscriptions", type_="foreignkey")
    op.create_foreign_key(
        "fk_subscriptions_branch_cascade",
        "subscriptions",
        "branches",
        ["branch_id"],
        ["branch_id"],
        ondelete="CASCADE",
    )
    op.drop_constraint("subscriptions_tariff_id_fkey", "subscriptions", type_="foreignkey")
    op.create_foreign_key(
        "fk_subscriptions_tariff_cascade",
        "subscriptions",
        "tariffs",
        ["tariff_id"],
        ["tariff_id"],
        ondelete="CASCADE",
    )
    op.drop_constraint("subscriptions_subscription_status_id_fkey", "subscriptions", type_="foreignkey")
    op.create_foreign_key(
        "fk_subscriptions_status_cascade",
        "subscriptions",
        "subscription_statuses",
        ["subscription_status_id"],
        ["subscription_status_id"],
        ondelete="CASCADE",
    )

    # visits
    op.drop_constraint("visits_user_id_fkey", "visits", type_="foreignkey")
    op.create_foreign_key(
        "fk_visits_user_cascade", "visits", "users", ["user_id"], ["user_id"], ondelete="CASCADE"
    )
    op.drop_constraint("visits_branch_id_fkey", "visits", type_="foreignkey")
    op.create_foreign_key(
        "fk_visits_branch_cascade", "visits", "branches", ["branch_id"], ["branch_id"], ondelete="CASCADE"
    )

    # sessions
    op.drop_constraint("sessions_user_id_fkey", "sessions", type_="foreignkey")
    op.create_foreign_key(
        "fk_sessions_user_cascade", "sessions", "users", ["user_id"], ["user_id"], ondelete="CASCADE"
    )

    # employee_branches
    op.drop_constraint("employee_branches_employee_id_fkey", "employee_branches", type_="foreignkey")
    op.create_foreign_key(
        "fk_employee_branches_employee_cascade",
        "employee_branches",
        "employees",
        ["employee_id"],
        ["employee_id"],
        ondelete="CASCADE",
    )
    op.drop_constraint("employee_branches_branch_id_fkey", "employee_branches", type_="foreignkey")
    op.create_foreign_key(
        "fk_employee_branches_branch_cascade",
        "employee_branches",
        "branches",
        ["branch_id"],
        ["branch_id"],
        ondelete="CASCADE",
    )


def downgrade() -> None:
    # employee_branches
    op.drop_constraint("fk_employee_branches_branch_cascade", "employee_branches", type_="foreignkey")
    op.drop_constraint("fk_employee_branches_employee_cascade", "employee_branches", type_="foreignkey")
    op.create_foreign_key(
        "employee_branches_branch_id_fkey", "employee_branches", "branches", ["branch_id"], ["branch_id"]
    )
    op.create_foreign_key(
        "employee_branches_employee_id_fkey",
        "employee_branches",
        "employees",
        ["employee_id"],
        ["employee_id"],
    )

    # sessions
    op.drop_constraint("fk_sessions_user_cascade", "sessions", type_="foreignkey")
    op.create_foreign_key("sessions_user_id_fkey", "sessions", "users", ["user_id"], ["user_id"])

    # visits
    op.drop_constraint("fk_visits_branch_cascade", "visits", type_="foreignkey")
    op.drop_constraint("fk_visits_user_cascade", "visits", type_="foreignkey")
    op.create_foreign_key("visits_branch_id_fkey", "visits", "branches", ["branch_id"], ["branch_id"])
    op.create_foreign_key("visits_user_id_fkey", "visits", "users", ["user_id"], ["user_id"])

    # subscriptions
    op.drop_constraint("fk_subscriptions_status_cascade", "subscriptions", type_="foreignkey")
    op.drop_constraint("fk_subscriptions_tariff_cascade", "subscriptions", type_="foreignkey")
    op.drop_constraint("fk_subscriptions_branch_cascade", "subscriptions", type_="foreignkey")
    op.drop_constraint("fk_subscriptions_user_cascade", "subscriptions", type_="foreignkey")
    op.create_foreign_key(
        "subscriptions_subscription_status_id_fkey",
        "subscriptions",
        "subscription_statuses",
        ["subscription_status_id"],
        ["subscription_status_id"],
    )
    op.create_foreign_key("subscriptions_tariff_id_fkey", "subscriptions", "tariffs", ["tariff_id"], ["tariff_id"])
    op.create_foreign_key("subscriptions_branch_id_fkey", "subscriptions", "branches", ["branch_id"], ["branch_id"])
    op.create_foreign_key("subscriptions_user_id_fkey", "subscriptions", "users", ["user_id"], ["user_id"])

    # promotion junctions
    op.drop_constraint("fk_promotion_tariffs_tariff_cascade", "promotion_tariffs", type_="foreignkey")
    op.drop_constraint("fk_promotion_tariffs_promotion_cascade", "promotion_tariffs", type_="foreignkey")
    op.create_foreign_key(
        "promotion_tariffs_tariff_id_fkey", "promotion_tariffs", "tariffs", ["tariff_id"], ["tariff_id"]
    )
    op.create_foreign_key(
        "promotion_tariffs_promotion_id_fkey",
        "promotion_tariffs",
        "promotions",
        ["promotion_id"],
        ["promotion_id"],
    )
    op.drop_constraint("fk_promotion_branches_branch_cascade", "promotion_branches", type_="foreignkey")
    op.drop_constraint("fk_promotion_branches_promotion_cascade", "promotion_branches", type_="foreignkey")
    op.create_foreign_key(
        "promotion_branches_branch_id_fkey",
        "promotion_branches",
        "branches",
        ["branch_id"],
        ["branch_id"],
    )
    op.create_foreign_key(
        "promotion_branches_promotion_id_fkey",
        "promotion_branches",
        "promotions",
        ["promotion_id"],
        ["promotion_id"],
    )

    # promotions
    op.drop_constraint("fk_promotions_discount_type_cascade", "promotions", type_="foreignkey")
    op.create_foreign_key(
        "promotions_discount_type_id_fkey",
        "promotions",
        "discount_types",
        ["discount_type_id"],
        ["discount_type_id"],
    )

    # tariffs
    op.drop_constraint("fk_tariffs_validity_period_cascade", "tariffs", type_="foreignkey")
    op.drop_constraint("fk_tariffs_tariff_type_cascade", "tariffs", type_="foreignkey")
    op.create_foreign_key(
        "tariffs_tariff_validity_period_id_fkey",
        "tariffs",
        "tariff_validity_periods",
        ["tariff_validity_period_id"],
        ["tariff_validity_period_id"],
    )
    op.create_foreign_key(
        "tariffs_tariff_type_id_fkey",
        "tariffs",
        "tariff_types",
        ["tariff_type_id"],
        ["tariff_type_id"],
    )

    # branches
    op.drop_constraint("fk_branches_district_cascade", "branches", type_="foreignkey")
    op.create_foreign_key(
        "branches_district_id_fkey", "branches", "districts", ["district_id"], ["district_id"]
    )
