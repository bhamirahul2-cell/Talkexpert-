import os
from fastapi import FastAPI, Depends, HTTPException, Header, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from jose import jwt, JWTError
import razorpay

from .database import Base, engine, get_db
from .models import User, ExpertProfile, Booking, Payment
from .schemas import RegisterIn, LoginIn, ExpertIn, BookingIn, VerifyPaymentIn
from .security import hash_password, verify_password, make_token, SECRET_KEY, ALGORITHM

Base.metadata.create_all(bind=engine)
app = FastAPI(title="TalkExpert API", version="0.2.0")

RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID", "")
RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET", "")
RAZORPAY_WEBHOOK_SECRET = os.getenv("RAZORPAY_WEBHOOK_SECRET", "")

def get_razorpay_client():
    if not RAZORPAY_KEY_ID or not RAZORPAY_KEY_SECRET:
        raise HTTPException(503, "Payment gateway is not configured. Add Razorpay TEST keys on the server.")
    return razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))

def current_user(authorization: str | None = Header(default=None), db: Session = Depends(get_db)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "Bearer token required")
    try:
        payload = jwt.decode(authorization[7:], SECRET_KEY, algorithms=[ALGORITHM])
        user = db.get(User, int(payload["sub"]))
    except (JWTError, ValueError, KeyError):
        raise HTTPException(401, "Invalid or expired token")
    if not user or not user.active:
        raise HTTPException(401, "Account unavailable")
    return user

def require_admin(user: User = Depends(current_user)):
    if user.role != "admin":
        raise HTTPException(403, "Admin access required")
    return user

def mark_payment_captured(db: Session, payment_row: Payment, payment_id: str):
    payment_row.razorpay_payment_id = payment_id
    payment_row.status = "paid"
    booking = db.get(Booking, payment_row.booking_id)
    if booking:
        booking.payment_status = "paid"
        booking.status = "paid"
    db.commit()

@app.get("/health")
def health():
    return {"status": "ok", "mode": "starter"}

@app.post("/auth/register")
def register(data: RegisterIn, db: Session = Depends(get_db)):
    if data.role not in ("user", "expert"):
        raise HTTPException(400, "Role must be user or expert")
    email = data.email.lower()
    if db.query(User).filter_by(email=email).first():
        raise HTTPException(409, "Email already registered")
    user = User(name=data.name, email=email, password_hash=hash_password(data.password), role=data.role)
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"message": "Account created", "user_id": user.id, "role": user.role}

@app.post("/auth/login")
def login(data: LoginIn, db: Session = Depends(get_db)):
    user = db.query(User).filter_by(email=data.email.lower()).first()
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(401, "Incorrect email or password")
    if not user.active:
        raise HTTPException(403, "Account disabled")
    return {"access_token": make_token(user.id, user.role), "token_type": "bearer",
            "user": {"id": user.id, "name": user.name, "role": user.role}}

@app.get("/me")
def me(user: User = Depends(current_user)):
    return {"id": user.id, "name": user.name, "email": user.email, "role": user.role}

@app.post("/experts/profile")
def create_expert_profile(data: ExpertIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    if user.role != "expert":
        raise HTTPException(403, "Expert account required")
    if db.query(ExpertProfile).filter_by(user_id=user.id).first():
        raise HTTPException(409, "Profile already submitted")
    profile = ExpertProfile(user_id=user.id, category=data.category, bio=data.bio,
                            credentials_note=data.credentials_note, approved=False)
    db.add(profile)
    db.commit()
    return {"message": "Profile submitted for admin review"}

@app.get("/experts")
def list_experts(db: Session = Depends(get_db)):
    rows = db.query(ExpertProfile, User).join(User, User.id == ExpertProfile.user_id).filter(
        ExpertProfile.approved == True, User.active == True
    ).all()
    return [{"expert_id": u.id, "name": u.name, "category": p.category, "bio": p.bio}
            for p, u in rows]

@app.post("/bookings")
def create_booking(data: BookingIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    if user.role != "user":
        raise HTTPException(403, "Only user accounts can book experts")
    profile = db.query(ExpertProfile).filter_by(user_id=data.expert_id, approved=True).first()
    if not profile:
        raise HTTPException(404, "Approved expert not found")
    booking = Booking(user_id=user.id, expert_id=data.expert_id, amount_paise=10000)
    db.add(booking)
    db.commit()
    db.refresh(booking)
    return {"booking_id": booking.id, "amount_inr": 100, "payment_status": "pending"}

@app.post("/bookings/{booking_id}/payment/order")
def create_payment_order(booking_id: int, user: User = Depends(current_user),
                         db: Session = Depends(get_db)):
    booking = db.get(Booking, booking_id)
    if not booking or booking.user_id != user.id:
        raise HTTPException(404, "Booking not found")
    if booking.payment_status == "paid":
        raise HTTPException(409, "Booking is already paid")
    existing = db.query(Payment).filter_by(booking_id=booking.id).first()
    if existing and existing.status == "created":
        return {"key_id": RAZORPAY_KEY_ID, "order_id": existing.razorpay_order_id,
                "amount": existing.amount_paise, "currency": "INR", "booking_id": booking.id}
    client = get_razorpay_client()
    try:
        order = client.order.create({
            "amount": 10000, "currency": "INR",
            "receipt": f"talkexpert_booking_{booking.id}",
            "notes": {"booking_id": str(booking.id), "user_id": str(user.id)}
        })
    except Exception:
        raise HTTPException(502, "Could not create payment order. Please try again.")
    if existing:
        existing.razorpay_order_id = order["id"]
        existing.razorpay_payment_id = None
        existing.amount_paise = 10000
        existing.status = "created"
        payment_row = existing
    else:
        payment_row = Payment(booking_id=booking.id, razorpay_order_id=order["id"],
                              amount_paise=10000, status="created")
        db.add(payment_row)
    db.commit()
    return {"key_id": RAZORPAY_KEY_ID, "order_id": order["id"],
            "amount": 10000, "currency": "INR", "booking_id": booking.id}

@app.post("/payments/verify")
def verify_payment(data: VerifyPaymentIn, user: User = Depends(current_user),
                   db: Session = Depends(get_db)):
    booking = db.get(Booking, data.booking_id)
    if not booking or booking.user_id != user.id:
        raise HTTPException(404, "Booking not found")
    payment_row = db.query(Payment).filter_by(
        booking_id=booking.id, razorpay_order_id=data.razorpay_order_id
    ).first()
    if not payment_row:
        raise HTTPException(400, "Payment order does not match this booking")
    client = get_razorpay_client()
    try:
        client.utility.verify_payment_signature({
            "razorpay_order_id": data.razorpay_order_id,
            "razorpay_payment_id": data.razorpay_payment_id,
            "razorpay_signature": data.razorpay_signature
        })
        payment_info = client.payment.fetch(data.razorpay_payment_id)
    except Exception:
        raise HTTPException(400, "Payment signature or payment status could not be verified")
    if (payment_info.get("order_id") != payment_row.razorpay_order_id or
        payment_info.get("amount") != 10000 or
        payment_info.get("currency") != "INR" or
        payment_info.get("status") != "captured"):
        raise HTTPException(400, "Payment is not captured for the expected amount")
    mark_payment_captured(db, payment_row, data.razorpay_payment_id)
    return {"message": "Payment verified", "booking_id": booking.id,
            "payment_status": "paid", "consultation_unlocked": True}

@app.post("/payments/webhook")
async def payment_webhook(request: Request, x_razorpay_signature: str | None = Header(default=None),
                          db: Session = Depends(get_db)):
    if not RAZORPAY_WEBHOOK_SECRET:
        raise HTTPException(503, "Webhook secret is not configured")
    raw_body = await request.body()
    if not x_razorpay_signature:
        raise HTTPException(400, "Missing webhook signature")
    try:
        get_razorpay_client().utility.verify_webhook_signature(
            raw_body.decode("utf-8"), x_razorpay_signature, RAZORPAY_WEBHOOK_SECRET
        )
    except Exception:
        raise HTTPException(400, "Invalid webhook signature")
    try:
        event = await request.json()
        if event.get("event") != "payment.captured":
            return {"received": True, "processed": False}
        entity = event["payload"]["payment"]["entity"]
        order_id = entity.get("order_id")
        payment_id = entity.get("id")
        payment_row = db.query(Payment).filter_by(razorpay_order_id=order_id).first()
        if (payment_row and entity.get("amount") == 10000 and
            entity.get("currency") == "INR" and entity.get("status") == "captured"):
            mark_payment_captured(db, payment_row, payment_id)
            return {"received": True, "processed": True}
    except (KeyError, TypeError, ValueError):
        raise HTTPException(400, "Invalid webhook payload")
    return {"received": True, "processed": False}

@app.get("/admin/experts")
def pending_experts(admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    rows = db.query(ExpertProfile, User).join(User, User.id == ExpertProfile.user_id).all()
    return [{"profile_id": p.id, "user_id": u.id, "name": u.name, "email": u.email,
             "category": p.category, "credentials_note": p.credentials_note, "approved": p.approved}
            for p, u in rows]

@app.post("/admin/experts/{profile_id}/approve")
def approve_expert(profile_id: int, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    profile = db.get(ExpertProfile, profile_id)
    if not profile:
        raise HTTPException(404, "Profile not found")
    profile.approved = True
    db.commit()
    return {"message": "Expert approved"}

@app.post("/admin/users/{user_id}/disable")
def disable_user(user_id: int, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    target = db.get(User, user_id)
    if not target:
        raise HTTPException(404, "User not found")
    if target.role == "admin":
        raise HTTPException(400, "Cannot disable admin")
    target.active = False
    db.commit()
    return {"message": "Account disabled"}

@app.get("/admin/payments")
def admin_payments(admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    rows = db.query(Payment).order_by(Payment.id.desc()).all()
    return [{"payment_id": p.id, "booking_id": p.booking_id, "order_id": p.razorpay_order_id,
             "gateway_payment_id": p.razorpay_payment_id, "amount_inr": p.amount_paise / 100,
             "status": p.status} for p in rows]

# Serve the TalkExpert frontend from the same origin as the API.
app.mount("/static", StaticFiles(directory="static"), name="static")
@app.get("/", include_in_schema=False)
def frontend():
    return FileResponse("static/index.html")
