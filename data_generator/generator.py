import json
import random
from datetime import datetime, timedelta
from faker import Faker
import networkx as nx
import pandas as pd

fake = Faker('en_IN')

BANKS = ["HDFC BANK", "SBI", "ICICI BANK", "AXIS BANK", "PUNB", "KOTAK"]
CITIES = ["Delhi", "Mumbai", "Hyderabad", "Bengaluru", "Kolkata", "Jaipur"]

def generate_base_graph(num_accounts=40):
    G = nx.DiGraph()
    accounts = []
    
    for i in range(num_accounts):
        acc_id = f"ACC_{1000 + i}"
        bank = random.choice(BANKS)
        node_data = {
            "acc_id": acc_id,
            "holder_name": fake.name(),
            "bank": bank,
            "ifsc": f"{bank[:4]}000{random.randint(1000, 9999)}",
            "city": random.choice(CITIES),
            "ip_address": fake.ipv4(),
            "is_dormant": random.choice([True] + [False]*9)
        }
        G.add_node(acc_id, **node_data)
        accounts.append(node_data)
        
    return G, accounts

def inject_fraud_patterns(G, accounts):
    injected_txns = []

    # 1. Mule Chain & Layering
    v, m1, m2 = accounts[0]['acc_id'], accounts[1]['acc_id'], accounts[2]['acc_id']
    injected_txns.extend([
        {"sender": v, "receiver": m1, "amount": 150000, "pattern": "MULE_CHAIN_LAYER_1", "delay_sec": 2},
        {"sender": m1, "receiver": m2, "amount": 140000, "pattern": "MULE_CHAIN_LAYER_2", "delay_sec": 5},
    ])

    # 2. Fan-Out Splitting
    f_source = accounts[3]['acc_id']
    for idx in range(4, 8):
        injected_txns.append({
            "sender": f_source, "receiver": accounts[idx]['acc_id'], 
            "amount": 45000, "pattern": "FAN_OUT_SPLIT", "delay_sec": 8 + idx
        })

    # 3. Dormant Reactivation
    dormant_acc = [a for a in accounts if a['is_dormant']][0]['acc_id']
    injected_txns.append({
        "sender": accounts[9]['acc_id'], "receiver": dormant_acc,
        "amount": 250000, "pattern": "DORMANT_REACTIVATION", "delay_sec": 20
    })

    for it in injected_txns:
        G.add_edge(it['sender'], it['receiver'], amount=it['amount'], pattern=it['pattern'])

    return injected_txns

def create_full_dataset():
    G, accounts = generate_base_graph(50)
    fraud_specs = inject_fraud_patterns(G, accounts)
    
    stream = []
    now = datetime.now()

    for i in range(25):
        s, r = random.sample(accounts, 2)
        stream.append({
            "txn_id": f"TXN_{10000 + i}",
            "timestamp": (now - timedelta(seconds=120 - i*4)).strftime("%H:%M:%S"),
            "sender": s['acc_id'],
            "receiver": r['acc_id'],
            "amount": random.randint(1000, 25000),
            "bank": r['bank'],
            "is_injected": False,
            "pattern": "NORMAL"
        })

    for i, f in enumerate(fraud_specs):
        r_node = G.nodes[f['receiver']]
        stream.append({
            "txn_id": f"TXN_FRAUD_{i+1}",
            "timestamp": (now - timedelta(seconds=40 - f['delay_sec'])).strftime("%H:%M:%S"),
            "sender": f['sender'],
            "receiver": f['receiver'],
            "amount": f['amount'],
            "bank": r_node['bank'],
            "is_injected": True,
            "pattern": f['pattern']
        })

    stream.sort(key=lambda x: x['timestamp'])

    df = pd.DataFrame(stream)
    df.to_json("synthetic_stream.json", orient="records", indent=2)
    print(f"Dataset generated successfully! Exported {len(stream)} records to 'synthetic_stream.json'.")

if __name__ == "__main__":
    create_full_dataset()