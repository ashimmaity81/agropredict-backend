
from fastapi import APIRouter, HTTPException
from database import users_collection
from models import UserSignup, UserLogin
from passlib.context import CryptContext
from jose import jwt
import os
import random
import smtplib
from email.mime.text import MIMEText

router = APIRouter()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
SECRET_KEY = os.getenv("SECRET_KEY")

# =========================
# 🔐 OTP STORE (Temporary)
# =========================
otp_store = {}

# =========================
# 📧 SEND OTP EMAIL
# =========================
def send_otp_email(to_email, otp):
    sender_email = os.getenv("EMAIL")
    sender_password = os.getenv("EMAIL_PASSWORD")

    if not sender_email or not sender_password:
        raise HTTPException(status_code=500, detail="Email config missing in .env")

    msg = MIMEText(f"Your OTP for password reset is: {otp}")
    msg["Subject"] = "Password Reset OTP"
    msg["From"] = sender_email
    msg["To"] = to_email

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, to_email, msg.as_string())
        server.quit()
    except Exception as e:
        print("❌ Email Error:", e)
        raise HTTPException(status_code=500, detail="Failed to send OTP")


# 🔒 Hash password
def hash_password(password: str):
    return pwd_context.hash(password[:72])


# 🔍 Verify password
def verify_password(plain: str, hashed: str):
    return pwd_context.verify(plain, hashed)


# 🔐 Get current user
def get_current_user(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        email = payload.get("email")

        user = users_collection.find_one({"email": email})
        if not user:
            raise HTTPException(status_code=401, detail="User not found")

        return user

    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")


# =========================
# ✅ SIGNUP
# =========================
@router.post("/signup")
def signup(user: UserSignup):
    try:
        existing = users_collection.find_one({"email": user.email})

        if existing:
            raise HTTPException(status_code=400, detail="User already exists")

        users_collection.insert_one({
            "name": user.name,
            "email": user.email,
            "password": hash_password(user.password)
        })

        return {"message": "Signup successful"}

    except HTTPException:
        raise
    except Exception as e:
        print("❌ ERROR (signup):", e)
        raise HTTPException(status_code=500, detail="Server error")


# =========================
# ✅ LOGIN
# =========================
# @router.post("/login")
# def login(user: UserLogin):
#     try:
#         db_user = users_collection.find_one({"email": user.email})

#         if not db_user:
#             raise HTTPException(status_code=400, detail="Invalid email")

#         if not verify_password(user.password, db_user["password"]):
#             raise HTTPException(status_code=400, detail="Wrong password")

#         token = jwt.encode(
#             {"email": db_user["email"]},
#             SECRET_KEY,
#             algorithm="HS256"
#         )

#         return {
#             "token": token,
#             "user": {
#                 "name": db_user["name"],
#                 "email": db_user["email"]
#             }
#         }

#     except HTTPException:
#         raise
#     except Exception as e:
#         print("❌ ERROR (login):", e)
#         raise HTTPException(status_code=500, detail="Server error")

@router.post("/login")
def login(user: UserLogin):
    try:
        db_user = users_collection.find_one({
            "$or": [
                {"email": user.email},
                {"name": user.email}   # ✅ added (use same field)
            ]
        })

        if not db_user:
            raise HTTPException(status_code=400, detail="Invalid email or name")

        if not verify_password(user.password, db_user["password"]):
            raise HTTPException(status_code=400, detail="Wrong password")

        token = jwt.encode(
            {"email": db_user["email"]},
            SECRET_KEY,
            algorithm="HS256"
        )

        return {
            "token": token,
            "user": {
                "name": db_user["name"],
                "email": db_user["email"]
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        print("❌ ERROR (login):", e)
        raise HTTPException(status_code=500, detail="Server error")


# =========================
# ✅ FORGOT PASSWORD (SEND OTP)
# =========================
@router.post("/forgot-password")
def forgot_password(data: dict):
    email = data.get("email")

    user = users_collection.find_one({"email": email})
    if not user:
        raise HTTPException(status_code=404, detail="Email not registered")

    otp = str(random.randint(100000, 999999))
    otp_store[email] = otp

    send_otp_email(email, otp)

    return {"message": "OTP sent successfully"}


# =========================
# ✅ VERIFY OTP
# =========================
@router.post("/verify-otp")
def verify_otp(data: dict):
    email = data.get("email")
    otp = data.get("otp")

    if email not in otp_store:
        raise HTTPException(status_code=400, detail="OTP not requested")

    if otp_store[email] != otp:
        raise HTTPException(status_code=400, detail="Invalid OTP")

    return {"message": "OTP verified"}


# =========================
# ✅ RESET PASSWORD
# =========================
@router.post("/reset-password")
def reset_password(data: dict):
    email = data.get("email")
    new_password = data.get("new_password")

    if email not in otp_store:
        raise HTTPException(status_code=400, detail="Unauthorized request")

    users_collection.update_one(
        {"email": email},
        {"$set": {"password": hash_password(new_password)}}
    )

    # Remove OTP after use
    del otp_store[email]

    return {"message": "Password reset successful"}


# =========================
# ✅ UPDATE NAME
# =========================
@router.put("/update-name")
def update_name(data: dict):
    try:
        user = get_current_user(data["token"])

        users_collection.update_one(
            {"email": user["email"]},
            {"$set": {"name": data["name"]}}
        )

        return {"message": "Name updated"}

    except HTTPException:
        raise
    except Exception as e:
        print("❌ ERROR (update-name):", e)
        raise HTTPException(status_code=500, detail="Server error")


# =========================
# ✅ CHANGE PASSWORD (UNCHANGED)
# =========================
@router.put("/change-password")
def change_password(data: dict):
    try:
        user = get_current_user(data["token"])

        if not verify_password(data["old_password"], user["password"]):
            raise HTTPException(status_code=400, detail="Wrong old password")

        users_collection.update_one(
            {"email": user["email"]},
            {"$set": {"password": hash_password(data["new_password"])}}
        )

        return {"message": "Password updated"}

    except HTTPException:
        raise
    except Exception as e:
        print("❌ ERROR (change-password):", e)
        raise HTTPException(status_code=500, detail="Server error")