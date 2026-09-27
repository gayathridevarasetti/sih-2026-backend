import random
import numpy as np
from sklearn.ensemble import IsolationForest

# Major Indian Cities Database with Coordinates
CITIES_DB = [
    {"city": "Mumbai", "lat": 19.0760, "lng": 72.8777, "state": "Maharashtra"},
    {"city": "Delhi", "lat": 28.6139, "lng": 77.2090, "state": "Delhi"},
    {"city": "Bengaluru", "lat": 12.9716, "lng": 77.5946, "state": "Karnataka"},
    {"city": "Hyderabad", "lat": 17.3850, "lng": 78.4867, "state": "Telangana"},
    {"city": "Kolkata", "lat": 22.5726, "lng": 88.3639, "state": "West Bengal"},
    {"city": "Chennai", "lat": 13.0827, "lng": 80.2707, "state": "Tamil Nadu"},
    {"city": "Ahmedabad", "lat": 23.0225, "lng": 72.5714, "state": "Gujarat"},
    {"city": "Pune", "lat": 18.5204, "lng": 73.8567, "state": "Maharashtra"},
]

class FraudDetectionEngine:
    def __init__(self):
        # Initialize ML anomaly detection model
        self.model = IsolationForest(contamination=0.15, random_state=42)
        # Train baseline on typical transaction amounts
        baseline_amounts = np.array([[2000], [5000], [12000], [8000], [15000], [200000], [180000], [250000]])
        self.model.fit(baseline_amounts)

    def predict_location(self, txn: dict) -> dict:
        """
        Extracts or simulates geographic location details, IP address, 
        and location-based anomaly risk.
        """
        # Pick location from transaction payload or fallback to random city node
        city_data = txn.get("location_data")
        if not city_data:
            city_data = random.choice(CITIES_DB)

        ip_address = txn.get("ip_address", f"{random.randint(10, 192)}.{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}")
        is_foreign = txn.get("is_foreign_ip", False)
        is_impossible_travel = txn.get("impossible_travel", False)

        return {
            "city": city_data["city"],
            "lat": city_data["lat"],
            "lng": city_data["lng"],
            "state": city_data["state"],
            "ip": ip_address,
            "foreign_ip": is_foreign,
            "impossible_travel": is_impossible_travel
        }

    def analyze_transaction(self, txn: dict) -> dict:
        amount = txn.get("amount", 0)
        pattern = txn.get("pattern", "NORMAL")

        # 1. Location Analytics
        geo = self.predict_location(txn)

        # 2. Rule-Based Scoring
        score = 15
        reasons = []

        if pattern == "MULE_CHAIN_LAYER_2":
            score = 96
            reasons.append("Rapid Fan-Out Layering in Mule Network (Window < 5s)")
        elif pattern == "FAN_OUT_SPLIT":
            score = 92
            reasons.append("Structuring: Single source splitting funds to multiple accounts")
        elif pattern == "DORMANT_REACTIVATION":
            score = 88
            reasons.append("Dormant account reactivation: >300 days idle, sudden high credit")
        elif pattern == "CIRCULAR_RING":
            score = 94
            reasons.append("Circular transfer loop detected across multiple accounts")
        elif pattern == "MULE_CHAIN_LAYER_1":
            score = 91
            reasons.append("High amount transfer to unrecognized primary mule node")

        # Location Risk Enhancements
        if geo["impossible_travel"]:
            score += 25
            reasons.append(f"Geo Anomaly: Impossible travel detected from {geo['city']}")
        elif geo["foreign_ip"]:
            score += 20
            reasons.append(f"High-Risk IP: Cross-border transfer initiated via foreign node ({geo['ip']})")

        # 3. Machine Learning Anomaly Detection Layer
        ml_pred = self.model.predict([[amount]])[0]
        if ml_pred == -1 and score < 70:
            score += 35
            reasons.append("Machine Learning: Anomaly score spiked above baseline velocity")

        score = min(max(score, 5), 98)

        if score >= 90:
            risk_level = "CRITICAL"
        elif score >= 70:
            risk_level = "HIGH"
        elif score >= 45:
            risk_level = "MEDIUM"
        else:
            risk_level = "NORMAL"

        reason_str = " | ".join(reasons) if reasons else "Normal transaction pattern"

        # Return full payload required by React Dashboard (NetworkGraph + Map)
        return {
            "id": txn.get("id", f"TXN_{random.randint(10000, 99999)}"),
            "time": txn.get("time", "Just now"),
            "sender": txn.get("sender", "ACC_UNKNOWN"),
            "receiver": txn.get("receiver", "ACC_UNKNOWN"),
            "amount": amount,
            "bank": txn.get("bank", "HDFC Bank"),
            "score": score,
            "risk": risk_level,
            "reason": reason_str,
            "city": geo["city"],
            "lat": geo["lat"],
            "lng": geo["lng"],
            "ip": geo["ip"]
        }

detector = FraudDetectionEngine()