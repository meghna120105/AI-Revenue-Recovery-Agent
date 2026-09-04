"""
generate_data.py
-----------------
Generates a SYNTHETIC dataset of Indian payment transactions for the AI
Revenue Recovery Agent project - v2, materially different from the first
dataset: more customers, more transactions, a 6-month window with a
festive-season spike, and multiple merchant verticals (not just one generic
store), so the failure/recovery patterns look like a real multi-merchant
platform rather than a single shop.

This data is entirely fabricated for demo purposes. No real customer or
payment data is used anywhere in this project.

Run:
    python data/generate_data.py

Output:
    data/payments.csv
"""

import random
from datetime import datetime, timedelta

import numpy as np
import pandas as pd

random.seed(7)
np.random.seed(7)

# --------------------------------------------------------------------------
# Reference lists used to build realistic-looking synthetic records
# --------------------------------------------------------------------------

FIRST_NAMES = [
    "Rahul", "Priya", "Amit", "Sneha", "Vikram", "Ananya", "Rohan", "Kavya",
    "Arjun", "Divya", "Karthik", "Neha", "Siddharth", "Pooja", "Aditya",
    "Ishita", "Manish", "Riya", "Suresh", "Meera", "Varun", "Nisha",
    "Gaurav", "Shreya", "Rajesh", "Anjali", "Kunal", "Swati", "Deepak",
    "Tanvi", "Harsh", "Simran", "Nikhil", "Preeti", "Sanjay", "Kiran",
    "Abhishek", "Lakshmi", "Vivek", "Radhika", "Farhan", "Ayesha", "Imran",
    "Zoya", "Joseph", "Maria", "Thomas", "Sunita", "Ramesh", "Geeta",
]

LAST_NAMES = [
    "Sharma", "Verma", "Patel", "Reddy", "Nair", "Gupta", "Iyer", "Singh",
    "Menon", "Rao", "Kapoor", "Joshi", "Chowdhury", "Malhotra", "Pillai",
    "Agarwal", "Bose", "Desai", "Kulkarni", "Mehta", "Khan", "Fernandes",
    "Thomas", "Pandey", "Bhatt",
]

CITIES = [
    "Mumbai", "Bengaluru", "Delhi", "Pune", "Hyderabad", "Chennai",
    "Kolkata", "Ahmedabad", "Jaipur", "Lucknow",
]
CITY_WEIGHTS = [0.18, 0.17, 0.14, 0.10, 0.10, 0.09, 0.07, 0.06, 0.05, 0.04]

MERCHANT_CATEGORIES = [
    "E-commerce", "Food Delivery", "Ride-Hailing", "SaaS Subscription", "Travel & Hotels",
]
MERCHANT_CATEGORY_WEIGHTS = [0.34, 0.24, 0.16, 0.14, 0.12]

DEVICE_TYPES = ["Mobile App", "Mobile Web", "Desktop Web"]
DEVICE_WEIGHTS = [0.62, 0.23, 0.15]

PAYMENT_METHODS = ["UPI", "Credit Card", "Debit Card", "Netbanking", "Wallet"]
# Weighted so UPI dominates, mirroring real Indian payment mix
PAYMENT_METHOD_WEIGHTS = [0.46, 0.19, 0.18, 0.09, 0.08]

FAILURE_REASONS = [
    "Insufficient Funds",
    "Card Declined",
    "Expired Card",
    "Network Failure",
    "Authentication Failure",
    "Bank Server Issue",
    "Unknown Error",
]
FAILURE_REASON_WEIGHTS = [0.22, 0.19, 0.09, 0.19, 0.15, 0.12, 0.04]

CUSTOMER_HISTORY_LEVELS = ["New Customer", "Occasional Buyer", "Regular Customer", "Loyal Customer"]
CUSTOMER_SEGMENTS = ["New", "Regular", "Premium"]

N_CUSTOMERS = 420
N_TRANSACTIONS = 1500
WINDOW_DAYS = 180          # 6 months of history
FESTIVE_SPIKE_START_DAY = 40   # a ~10 day "festive sale" window with more volume + more failures
FESTIVE_SPIKE_LEN = 10

# Typical order-value ranges per merchant vertical (INR), used to keep
# amounts realistic per category rather than one generic distribution.
CATEGORY_AMOUNT_PARAMS = {
    "E-commerce": (7.5, 0.65),
    "Food Delivery": (6.0, 0.45),
    "Ride-Hailing": (5.6, 0.40),
    "SaaS Subscription": (7.8, 0.35),
    "Travel & Hotels": (9.2, 0.55),
}


def build_customers(n_customers: int):
    """Create a pool of synthetic customers with a segment, history level, and city."""
    customers = []
    for i in range(1, n_customers + 1):
        segment = random.choices(CUSTOMER_SEGMENTS, weights=[0.32, 0.46, 0.22])[0]

        if segment == "Premium":
            history = random.choices(CUSTOMER_HISTORY_LEVELS, weights=[0.05, 0.15, 0.35, 0.45])[0]
        elif segment == "Regular":
            history = random.choices(CUSTOMER_HISTORY_LEVELS, weights=[0.10, 0.30, 0.40, 0.20])[0]
        else:  # New
            history = random.choices(CUSTOMER_HISTORY_LEVELS, weights=[0.55, 0.30, 0.10, 0.05])[0]

        name = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
        city = random.choices(CITIES, weights=CITY_WEIGHTS)[0]

        customers.append({
            "customer_id": f"CUST{i:04d}",
            "customer_name": name,
            "customer_segment": segment,
            "customer_history": history,
            "city": city,
        })
    return customers


def sample_amount(segment: str, category: str) -> float:
    """Sample a transaction amount (INR) based on customer segment AND merchant category."""
    mean, sigma = CATEGORY_AMOUNT_PARAMS[category]

    if segment == "Premium":
        mean += 0.6
    elif segment == "New":
        mean -= 0.4

    amount = np.random.lognormal(mean=mean, sigma=sigma)
    amount = max(99.0, min(amount, 89999.0))
    return round(amount, 2)


def sample_transaction_day(is_festive_weighted: bool) -> int:
    """Pick a day offset within the window, oversampling the festive-spike window."""
    if is_festive_weighted and random.random() < 0.30:
        return random.randint(FESTIVE_SPIKE_START_DAY, FESTIVE_SPIKE_START_DAY + FESTIVE_SPIKE_LEN)
    return random.randint(0, WINDOW_DAYS - 1)


def build_transactions(customers):
    rows = []
    txn_counter = 1
    now = datetime.now()

    for _ in range(N_TRANSACTIONS):
        customer = random.choice(customers)
        segment = customer["customer_segment"]
        history = customer["customer_history"]

        category = random.choices(MERCHANT_CATEGORIES, weights=MERCHANT_CATEGORY_WEIGHTS)[0]
        device = random.choices(DEVICE_TYPES, weights=DEVICE_WEIGHTS)[0]

        amount = sample_amount(segment, category)
        payment_method = random.choices(PAYMENT_METHODS, weights=PAYMENT_METHOD_WEIGHTS)[0]

        days_ago_offset = sample_transaction_day(is_festive_weighted=True)
        seconds_offset = random.randint(0, 86399)
        txn_date = now - timedelta(days=(WINDOW_DAYS - days_ago_offset), seconds=-seconds_offset)
        in_festive_window = FESTIVE_SPIKE_START_DAY <= days_ago_offset <= (FESTIVE_SPIKE_START_DAY + FESTIVE_SPIKE_LEN)

        # Base failure probability, adjusted by customer history, segment,
        # device (mobile web checkouts fail slightly more than native app),
        # and festive-season load (higher traffic -> more bank-side failures).
        base_fail_prob = 0.28
        if history == "Loyal Customer":
            base_fail_prob -= 0.12
        elif history == "New Customer":
            base_fail_prob += 0.10

        if segment == "Premium":
            base_fail_prob -= 0.04
        elif segment == "New":
            base_fail_prob += 0.05

        if device == "Mobile Web":
            base_fail_prob += 0.04
        if in_festive_window:
            base_fail_prob += 0.07

        base_fail_prob = min(max(base_fail_prob, 0.05), 0.70)
        is_failed = random.random() < base_fail_prob

        if is_failed:
            payment_status = "Failed"

            # During the festive spike, bank/network load issues dominate
            # more than usual (real-world pattern: infra strain, not
            # customer-side problems).
            if in_festive_window:
                weights = [0.16, 0.16, 0.07, 0.27, 0.14, 0.17, 0.03]
            else:
                weights = FAILURE_REASON_WEIGHTS

            failure_reason = random.choices(FAILURE_REASONS, weights=weights)[0]
            retry_count = random.choices([0, 1, 2, 3], weights=[0.35, 0.30, 0.22, 0.13])[0]

            # Whether the transaction was EVENTUALLY recovered after retry /
            # follow-up. This becomes the training label for the ML model.
            recovery_base = {
                "Network Failure": 0.76,
                "Bank Server Issue": 0.69,
                "Authentication Failure": 0.56,
                "Card Declined": 0.44,
                "Insufficient Funds": 0.34,
                "Expired Card": 0.29,
                "Unknown Error": 0.24,
            }[failure_reason]

            if history == "Loyal Customer":
                recovery_base += 0.12
            elif history == "New Customer":
                recovery_base -= 0.10

            if segment == "Premium":
                recovery_base += 0.08

            recovery_base -= 0.06 * retry_count  # customer fatigue

            recovery_prob = min(max(recovery_base, 0.03), 0.95)
            recovered_after_retry = int(random.random() < recovery_prob)
        else:
            payment_status = "Success"
            failure_reason = None
            retry_count = 0
            recovered_after_retry = None  # not applicable for successful txns

        rows.append({
            "transaction_id": f"TXN{txn_counter:05d}",
            "customer_id": customer["customer_id"],
            "customer_name": customer["customer_name"],
            "amount": amount,
            "currency": "INR",
            "payment_method": payment_method,
            "transaction_date": txn_date.strftime("%Y-%m-%d %H:%M:%S"),
            "payment_status": payment_status,
            "failure_reason": failure_reason,
            "customer_history": history,
            "retry_count": retry_count,
            "customer_segment": segment,
            "recovered_after_retry": recovered_after_retry,
            # extra context columns - not required by the analyzer, but
            # available for extra charts / filters if you want them
            "merchant_category": category,
            "city": customer["city"],
            "device_type": device,
        })
        txn_counter += 1

    return rows


def main():
    customers = build_customers(N_CUSTOMERS)
    rows = build_transactions(customers)
    df = pd.DataFrame(rows)
    df = df.sort_values("transaction_date").reset_index(drop=True)

    output_path = "data/payments.csv"
    df.to_csv(output_path, index=False)

    print(f"Generated {len(df)} synthetic transactions across {df['merchant_category'].nunique()} "
          f"merchant categories and {df['city'].nunique()} cities -> {output_path}")
    print(df["payment_status"].value_counts())


if __name__ == "__main__":
    main()
