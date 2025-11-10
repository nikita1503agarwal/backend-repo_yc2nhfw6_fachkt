import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
from database import create_document, get_documents, db
from schemas import Reservation, MenuItem, Order, OrderItem

app = FastAPI(title="Brew Haven API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Brew Haven Backend is running"}

# Health + DB test
@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
            response["database_name"] = getattr(db, 'name', None) or ("✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set")
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:80]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:80]}"
    return response

# -------- Reservations --------
@app.post("/api/reservations")
def create_reservation(reservation: Reservation):
    try:
        reservation_id = create_document("reservation", reservation)
        return {"status": "ok", "id": reservation_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# -------- Menu --------
@app.get("/api/menu", response_model=List[MenuItem])
def get_menu():
    # For simplicity we return static menu if DB empty; otherwise read from DB
    try:
        docs = get_documents("menuitem")
        items: List[MenuItem] = []
        for d in docs:
            d.pop("_id", None)
            items.append(MenuItem(**d))
        if items:
            return items
    except Exception:
        pass

    # Fallback sample menu
    fallback = [
        MenuItem(name="Espresso", description="Rich and bold single shot.", price=3.0, category="coffee", image="/images/espresso.jpg"),
        MenuItem(name="Cappuccino", description="Espresso with velvety milk foam.", price=4.5, category="coffee", image="/images/cappuccino.jpg"),
        MenuItem(name="Matcha Latte", description="Ceremonial grade matcha and milk.", price=5.0, category="tea", image="/images/matcha.jpg"),
        MenuItem(name="Blueberry Muffin", description="Buttery muffin with fresh blueberries.", price=3.5, category="bakery", image="/images/muffin.jpg"),
    ]
    return fallback

# -------- Orders / Payments (Mock) --------
class CheckoutRequest(BaseModel):
    items: List[OrderItem]

@app.post("/api/checkout")
def checkout(req: CheckoutRequest):
    # This is a mock payment flow. In production you'd integrate Stripe/PayPal.
    total = sum(i.price * i.quantity for i in req.items)
    return {"status": "requires_payment", "provider": "mock", "total": round(total, 2), "payment_url": "https://example.com/pay"}


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
