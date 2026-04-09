import json
import random
from datetime import datetime, timedelta
import os

# Create data directory if it doesn't exist
os.makedirs('data', exist_ok=True)

def generate_metrics():
    metrics = []
    base_date = datetime.now() - timedelta(days=14)
    
    # Base baselines
    activation = 22.5
    dau = 15000
    retention_d1 = 45.0
    crash_rate = 0.5
    latency_p95 = 200
    payment_success = 98.5
    feature_adoption = 5.0
    
    for i in range(14):
        current_date = (base_date + timedelta(days=i)).strftime('%Y-%m-%d')
        
        # Introduce anomaly on day 10 (index 9) for the V2 checkout feature bug
        if i >= 9:
            latency_p95 += random.uniform(300, 800)  # Huge latency spike
            crash_rate += random.uniform(1.5, 3.0)   # Crash rate spikes
            payment_success -= random.uniform(5.0, 15.0) # Payments fail due to latency/crash
            retention_d1 -= random.uniform(2.0, 5.0)  # Retention starts dropping
            feature_adoption += random.uniform(5.0, 10.0) # High adoption initially but buggy
        else:
            # Normal variance
            latency_p95 = max(150, latency_p95 + random.uniform(-20, 20))
            crash_rate = max(0.1, crash_rate + random.uniform(-0.1, 0.1))
            payment_success = min(99.9, payment_success + random.uniform(-0.5, 0.5))
            retention_d1 = min(100, max(0, retention_d1 + random.uniform(-1, 1)))
            activation = min(100, max(0, activation + random.uniform(-0.5, 0.5)))
            dau += int(random.uniform(-500, 800))
            feature_adoption = min(100, max(0, feature_adoption + random.uniform(-0.2, 0.5)))

        metrics.append({
            "date": current_date,
            "activation_conversion_pct": round(activation, 2),
            "dau": int(dau),
            "d1_retention_pct": round(retention_d1, 2),
            "crash_rate_pct": round(crash_rate, 2),
            "p95_api_latency_ms": round(latency_p95, 2),
            "payment_success_pct": round(payment_success, 2),
            "feature_adoption_pct": round(feature_adoption, 2)
        })
        
    with open('data/metrics.json', 'w') as f:
        json.dump(metrics, f, indent=4)
        
def generate_feedback():
    feedbacks = []
    
    # 20-50 short entries
    positive_templates = [
        "Love the new design!",
        "The new checkout is so slick.",
        "Much faster than before, great job.",
        "Looks very modern.",
        "Smooth experience."
    ]
    
    neutral_templates = [
        "It's okay, took a minute to find the new buttons.",
        "Nothing special, works fine.",
        "I didn't notice much difference.",
        "Seems alright."
    ]
    
    negative_templates = [
        "App crashed when I tried to pay!",
        "Payment keeps hanging on the loading screen.",
        "It says my card failed but it worked yesterday.",
        "Terrible update, latency is so high on the checkout page.",
        "Why did you change it? The old way actually worked.",
        "Timeout error every time I try to confirm purchase."
    ]
    
    # Days 1-9: Mostly positive/neutral
    for i in range(15):
        feedbacks.append({
            "id": f"fb_pre_{i}",
            "timestamp": (datetime.now() - timedelta(days=random.randint(5, 14))).isoformat(),
            "content": random.choice(positive_templates + neutral_templates),
            "rating": random.randint(3, 5)
        })
        
    # Days 10-14: Huge spike in negative feedback regarding payments and crashes
    for i in range(25):
        feedbacks.append({
            "id": f"fb_post_{i}",
            "timestamp": (datetime.now() - timedelta(days=random.randint(0, 4))).isoformat(),
            "content": random.choice(negative_templates),
            "rating": random.randint(1, 2)
        })
        
    # Shuffle
    random.shuffle(feedbacks)
    
    with open('data/feedback.json', 'w') as f:
        json.dump(feedbacks, f, indent=4)
        
def generate_release_notes():
    notes = """# Release Notes: V2.0 Checkout Flow Revamp (Date: T-10 days)

## Overview
Rollout of the new dynamic checkout flow designed to reduce friction and improve conversion.

## Changes
- Replaced legacy payment gateway integration with async microservices.
- Added animated UI transitions on checkout.
- Migrated the frontend to new API v3 endpoints.

## Known Risks
- The new async microservices rely on a message queue that occasionally spikes in latency under heavy load.
- Fallback payment routes were not fully load-tested.
- UI animations may cause memory leaks on older devices, potentially leading to increased crash rates.
"""
    with open('data/release_notes.txt', 'w') as f:
        f.write(notes)

if __name__ == "__main__":
    generate_metrics()
    generate_feedback()
    generate_release_notes()
    print("Mock data generated successfully in backend/data/")
