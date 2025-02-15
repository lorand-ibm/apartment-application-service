from django.utils.translation import gettext_lazy as _
from enumfields import Enum


class InstallmentType(Enum):
    PAYMENT_1 = "PAYMENT_1"
    PAYMENT_2 = "PAYMENT_2"
    PAYMENT_3 = "PAYMENT_3"
    PAYMENT_4 = "PAYMENT_4"
    PAYMENT_5 = "PAYMENT_5"
    PAYMENT_6 = "PAYMENT_6"
    PAYMENT_7 = "PAYMENT_7"
    REFUND = "REFUND"
    DOWN_PAYMENT = "DOWN_PAYMENT"
    LATE_PAYMENT_INTEREST = "LATE_PAYMENT_INTEREST"
    RIGHT_OF_RESIDENCE_FEE = "RIGHT_OF_RESIDENCE_FEE"
    FOR_INVOICING = "FOR_INVOICING"
    DEPOSIT = "DEPOSIT"
    RESERVATION_FEE = "RESERVATION_FEE"

    class Labels:
        PAYMENT_1 = _("1st payment")
        PAYMENT_2 = _("2nd payment")
        PAYMENT_3 = _("3rd payment")
        PAYMENT_4 = _("4th payment")
        PAYMENT_5 = _("5th payment")
        PAYMENT_6 = _("6th payment")
        PAYMENT_7 = _("7th payment")
        REFUND = _("refund")
        DOWN_PAYMENT = _("down payment")
        LATE_PAYMENT_INTEREST = _("late payment interest")
        RIGHT_OF_RESIDENCE_FEE = _("right of residence fee")
        FOR_INVOICING = _("for invoicing")
        DEPOSIT = _("deposit")
        RESERVATION_FEE = _("reservation fee")


class InstallmentUnit(Enum):
    EURO = "EURO"
    PERCENT = "PERCENT"

    class Labels:
        EURO = _("euro")
        PERCENT = _("percent")


class InstallmentPercentageSpecifier(Enum):
    SALES_PRICE = "SALES_PRICE"
    DEBT_FREE_SALES_PRICE = "DEBT_FREE_SALES_PRICE"
    DEBT_FREE_SALES_PRICE_FLEXIBLE = "DEBT_FREE_SALES_PRICE_FLEXIBLE"

    class Labels:
        SALES_PRICE = _("sales price")
        DEBT_FREE_SALES_PRICE = _("debt free sales price")
        DEBT_FREE_SALES_PRICE_FLEXIBLE = _("debt free sales price flexible")
