"""Response contract for a successful login (TC-002).

The public docs' example body only shows a handful of ``account`` fields;
the real endpoint returns a much larger account snapshot (verification/KYC
status, marketing consent, security question, etc. — see
test-cases/api/authentication/login.md#tc-002 for the full observed body
from the first verified run, 2026-07-09). This model reflects that *observed*
contract, not the docs' abbreviated sample. ``extra="forbid"`` on every
nested model turns "no undocumented fields" (TC-002) into schema validation:
any field added later fails this test until the model is updated
deliberately, rather than silently passing through unnoticed.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


def _to_kebab(field_name: str) -> str:
    return field_name.replace("_", "-")


class _KebabModel(BaseModel):
    """Base for API models whose JSON keys are kebab-case."""

    model_config = ConfigDict(alias_generator=_to_kebab, populate_by_name=True, extra="forbid")


class Country(_KebabModel):
    country_id: int
    name: str
    country_code: str


class Address(_KebabModel):
    address_id: int
    address_line_1: str
    address_line_2: str
    region_name: str
    country: Country
    post_code: str


class Name(_KebabModel):
    first: str
    last: str
    title_id: str
    title: str


class SecurityQuestion(_KebabModel):
    security_question_id: int
    security_question: str


class UserSecurityQuestion(_KebabModel):
    user_security_question_id: int
    question: SecurityQuestion


class MarketingPreferences(_KebabModel):
    product_casino_consent: bool
    product_exchange_consent: bool
    email_consent: bool
    sms_consent: bool
    consents_updated_at: datetime
    consents_update_required: bool


class Account(_KebabModel):
    id: int
    user_id: int
    name: Name
    date_of_birth: datetime
    email: str
    phone_number: str
    username: str
    balance: float
    free_funds: float
    exposure: float
    commission_credit: float
    status: str
    cashier_status: str
    casino_status: str
    virtuals_status: str
    language_id: int
    language: str
    address: Address
    currency_id: int
    currency: str
    odds_type_id: str
    odds_type: str
    bet_confirmation: bool
    display_p_and_l: bool
    exchange_type_id: str
    exchange_type: str
    odds_rounding: bool
    bonus_code: str
    deposit_terms: str
    user_security_question: UserSecurityQuestion
    mfa_enabled: bool
    last_login: datetime
    registration_time: datetime
    bet_slip_pinned: bool
    marketing_consent: bool
    affordability_info_provided: bool
    proof_of_address_status: str
    proof_of_identity_status: str
    edd_status: str
    responsible_gambling_interaction: str
    registration_vertical: str
    segment_category: str
    marketing_preferences: MarketingPreferences
    show_transactions_history_reminder: bool
    terms_and_conditions_accepted: bool


class LoginResponse(_KebabModel):
    session_token: str = Field(min_length=1)
    user_id: int
    role: str
    account: Account
    last_login: datetime
