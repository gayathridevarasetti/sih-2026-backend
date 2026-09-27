import asyncio
import json
import os

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from ai_engine import detector


app = FastAPI(
    title="CyberShield AI - Fraud Stream API"
)


# --------------------------------------------------
# CORS
# --------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --------------------------------------------------
# ROOT API
# --------------------------------------------------

@app.get("/")
def root():
    return {
        "status": "Online",
        "system": "CyberShield AI Backend v1.0"
    }


# --------------------------------------------------
# HEALTH CHECK
# --------------------------------------------------

@app.get("/api/health")
def health_check():
    return {
        "cfcfrms_pipeline": "CONNECTED",
        "latency_ms": 12
    }


# --------------------------------------------------
# WEBSOCKET LIVE FRAUD STREAM
# --------------------------------------------------

@app.websocket("/ws/live-stream")
async def websocket_endpoint(websocket: WebSocket):

    await websocket.accept()

    print("Client connected to WebSocket stream.")

    # Find synthetic_stream.json
    current_dir = os.path.dirname(os.path.abspath(__file__))

    data_path = os.path.join(
        current_dir,
        "..",
        "synthetic_stream.json"
    )

    data_path = os.path.abspath(data_path)

    print("Looking for dataset at:")
    print(data_path)

    # --------------------------------------------------
    # Check dataset
    # --------------------------------------------------

    if not os.path.exists(data_path):

        await websocket.send_json({
            "error": "Dataset not found. Run generator.py first!"
        })

        await websocket.close()

        return

    # --------------------------------------------------
    # Load transactions
    # --------------------------------------------------

    try:

        with open(
            data_path,
            "r",
            encoding="utf-8"
        ) as file:

            transactions = json.load(file)

    except Exception as error:

        print("Error loading dataset:", error)

        await websocket.send_json({
            "error": "Unable to load transaction dataset."
        })

        await websocket.close()

        return

    # --------------------------------------------------
    # Send transactions continuously
    # --------------------------------------------------

    try:

        while True:

            for txn in transactions:

                # --------------------------------------
                # AI fraud analysis
                # --------------------------------------

                analysis = detector.analyze_transaction(txn)


                # --------------------------------------
                # Transaction payload
                # --------------------------------------

                payload = {

                    # Transaction information
                    "id": txn.get(
                        "txn_id",
                        txn.get("id", "UNKNOWN")
                    ),

                    "time": txn.get(
                        "timestamp",
                        txn.get("time", "Just now")
                    ),

                    "sender": txn.get(
                        "sender",
                        "UNKNOWN"
                    ),

                    "receiver": txn.get(
                        "receiver",
                        "UNKNOWN"
                    ),

                    "amount": txn.get(
                        "amount",
                        0
                    ),

                    "bank": txn.get(
                        "bank",
                        "HDFC Bank"
                    ),


                    # ----------------------------------
                    # AI fraud information
                    # ----------------------------------

                    "score": analysis.get(
                        "score",
                        0
                    ),

                    "risk": analysis.get(
                        "risk",
                        "LOW"
                    ),

                    "reason": analysis.get(
                        "reason",
                        "No suspicious activity detected"
                    ),


                    # ----------------------------------
                    # Location information
                    # ----------------------------------

                    "city": analysis.get(
                        "city",
                        txn.get("city")
                    ),

                    "lat": analysis.get(
                        "lat",
                        txn.get("lat")
                    ),

                    "lng": analysis.get(
                        "lng",
                        txn.get("lng")
                    ),

                    "ip": analysis.get(
                        "ip",
                        txn.get("ip")
                    ),
                }


                # --------------------------------------
                # Send to React frontend
                # --------------------------------------

                await websocket.send_json(payload)

                print(
                    f"Sent: "
                    f"{payload['sender']} -> "
                    f"{payload['receiver']} | "
                    f"{payload['risk']}"
                )


                # Wait before next transaction
                await asyncio.sleep(2.5)


    except WebSocketDisconnect:

        print(
            "Client disconnected from WebSocket stream."
        )


    except Exception as error:

        print(
            "WebSocket error:",
            error
        )