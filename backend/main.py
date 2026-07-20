from fastapi import FastAPI
from api.network import router as network_router
from api.wallet import router as wallet_router
from api.transactions import router as transactions_router
from api.graph import router as graph_router
from api.features import router as features_router

app = FastAPI(
    title="Cross Chain Intelligence Platform",
    version="1.0.0"
)

# Routers ko app mein include karte hain
app.include_router(network_router)
app.include_router(wallet_router)
app.include_router(transactions_router)
app.include_router(graph_router)
app.include_router(features_router)


@app.get("/")
def home():
    return {
        "message": "Cross Chain Intelligence Platform Running Successfully"
    }