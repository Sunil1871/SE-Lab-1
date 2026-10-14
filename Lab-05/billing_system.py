"""Subscription billing system for managing plans and invoices."""
import calendar
import hashlib
import hmac
import os
import secrets
from datetime import date

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from lxml import etree
from mako.template import Template

PLANS = {"basic": 199, "pro": 499, "team": 999}
GST = 0.18
TRIAL_DAYS = 14
MAX_ATTEMPTS = 3

WEBHOOK_SECRET = os.environ.get("WEBHOOK_SECRET", "")
CARD_KEY = os.environ.get("CARD_KEY", "").encode()

subscriptions = {}

coupons = {
    "WELCOME10": {
        "percent": 10,
        "expires": date(2026, 12, 31),
    },
    "FRIENDS150": {
        "percent": 150,
        "expires": date(2027, 1, 31),
    },
}


def subscribe(user, plan, start):
    """Create a trial subscription for a valid plan."""
    if plan not in PLANS:
        raise ValueError("Invalid subscription plan")

    subscriptions[user] = {
        "plan": plan,
        "start": start,
        "status": "trial",
        "invoices": [],
    }
    return subscriptions[user]


def is_trial_over(user, today):
    """Check whether the trial period has ended."""
    elapsed_days = (today - subscriptions[user]["start"]).days
    return elapsed_days >= TRIAL_DAYS


def apply_coupon(amount, code, today):
    """Apply a valid coupon without creating a negative invoice."""
    coupon = coupons.get(code)

    if coupon is None or today >= coupon["expires"]:
        return amount

    discount_percent = min(coupon["percent"], 100)
    return amount - amount * discount_percent / 100


def invoice_amount(user, code=None, today=None):
    """Calculate the subscription invoice with tax and discount."""
    if today is None:
        today = date.today()

    plan_price = PLANS[subscriptions[user]["plan"]]
    total_with_tax = plan_price * (1 + GST)

    return apply_coupon(total_with_tax, code, today)


def next_billing_date(current):
    """Calculate the next billing date safely."""
    if current.month == 12:
        next_year = current.year + 1
        next_month = 1
    else:
        next_year = current.year
        next_month = current.month + 1

    last_day = calendar.monthrange(next_year, next_month)[1]
    next_day = min(current.day, last_day)

    return date(next_year, next_month, next_day)


def prorate_upgrade(user, new_plan, today, period_end):
    """Calculate the remaining-period upgrade cost."""
    if new_plan not in PLANS:
        raise ValueError("Invalid subscription plan")

    old_price = PLANS[subscriptions[user]["plan"]]
    new_price = PLANS[new_plan]
    days_left = max(0, (period_end - today).days)

    subscriptions[user]["plan"] = new_plan

    return max(0, new_price - old_price) * days_left / 30


def retry_payment(charge):
    """Retry a failed payment no more than the allowed attempts."""
    for attempt in range(1, MAX_ATTEMPTS + 1):
        if charge():
            return attempt

    return MAX_ATTEMPTS


def cancel_refund(user, days_used):
    """Calculate a prorated refund for a 30-day subscription."""
    price = PLANS[subscriptions[user]["plan"]]
    used_days = max(0, min(days_used, 30))
    unused_days = 30 - used_days

    return price * unused_days / 30


def coupon_code():
    """Generate a coupon code using a secure random choice."""
    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    suffix = "".join(secrets.choice(alphabet) for _ in range(6))

    return f"SAVE-{suffix}"


def active_users():
    """Return users whose subscriptions have no invoices."""
    return {
        user
        for user, subscription in subscriptions.items()
        if not subscription["invoices"]
    }


def encrypt_card(card_number):
    """Encrypt card data using authenticated AES-GCM encryption."""
    if len(CARD_KEY) not in (16, 24, 32):
        raise ValueError(
            "CARD_KEY must contain 16, 24, or 32 bytes"
        )

    nonce = os.urandom(12)
    cipher = AESGCM(CARD_KEY)
    ciphertext = cipher.encrypt(nonce, card_number.encode(), None)

    return (nonce + ciphertext).hex()


def verify_webhook(body, signature):
    """Verify a webhook signature using a safe comparison."""
    if not WEBHOOK_SECRET:
        raise ValueError(
            "WEBHOOK_SECRET environment variable is not set"
        )

    expected = hmac.new(
        WEBHOOK_SECRET.encode(),
        body,
        hashlib.sha256,
    ).hexdigest()

    return hmac.compare_digest(expected, signature)


def parse_webhook(xml_bytes):
    """Parse webhook XML with external entities disabled."""
    parser = etree.XMLParser(
        resolve_entities=False,
        no_network=True,
        load_dtd=False,
    )

    root = etree.fromstring(xml_bytes, parser=parser)

    return {
        "event": root.findtext("event"),
        "user": root.findtext("user"),
    }


def render_invoice(user, amount):
    """Render an invoice while escaping user-provided HTML."""
    if amount < 0:
        raise ValueError("Invoice amount cannot be negative")

    template = Template(
        "<h1>Invoice for ${user | h}</h1>"
        "<p>Total: Rs.${amount}</p>"
    )

    return template.render(user=user, amount=amount)


def main():
    """Run examples of the billing functions."""
    subscribe("asha", "pro", date(2026, 9, 1))
    subscribe(
        "<b onmouseover=alert(1)>ravi</b>",
        "basic",
        date(2026, 9, 20),
    )

    print(
        "Trial over on 09-15?",
        is_trial_over("asha", date(2026, 9, 15)),
    )

    print(
        "Pro invoice with WELCOME10:",
        invoice_amount("asha", "WELCOME10", date(2026, 10, 1)),
    )

    print(
        "Pro invoice with FRIENDS150:",
        invoice_amount("asha", "FRIENDS150", date(2026, 10, 1)),
    )

    print(
        "Coupon on expiry day:",
        invoice_amount("asha", "WELCOME10", date(2026, 12, 31)),
    )

    print(
        "Next billing date:",
        next_billing_date(date(2026, 10, 15)),
    )

    print(
        "Upgrade cost:",
        prorate_upgrade(
            "asha",
            "team",
            date(2027, 2, 18),
            date(2027, 2, 28),
        ),
    )

    calls = []

    def failed_charge():
        """Record a failed payment attempt."""
        calls.append(1)
        return False

    print("Payment attempts:", retry_payment(failed_charge))
    print("Refund after 25 days:", cancel_refund("asha", 25))
    print("Active users:", active_users())
    print("Coupon:", coupon_code())

    print(
        "Invoice HTML:",
        render_invoice("<b onmouseover=alert(1)>ravi</b>", 199),
    )

    print(
        "Webhook:",
        parse_webhook(
            b"<hook><event>paid</event><user>asha</user></hook>"
        ),
    )

    if WEBHOOK_SECRET:
        body = b"<x/>"
        signature = hmac.new(
            WEBHOOK_SECRET.encode(),
            body,
            hashlib.sha256,
        ).hexdigest()

        print("Webhook verified:", verify_webhook(body, signature))
    else:
        print("Webhook check skipped: set WEBHOOK_SECRET first")

    if len(CARD_KEY) in (16, 24, 32):
        first = encrypt_card("4111111111111111")
        second = encrypt_card("4111111111111111")

        print("Different ciphertexts:", first != second)
    else:
        print("Encryption skipped: set a valid CARD_KEY first")


if __name__ == "__main__":
    main()
