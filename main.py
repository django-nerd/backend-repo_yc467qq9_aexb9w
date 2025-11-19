import os
from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from bson import ObjectId

from database import db, create_document, get_documents
from schemas import User, Doctor, Patient, Appointment, Prescription

app = FastAPI(title="Hospital Management System API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Helpers
class IDModel(BaseModel):
    id: str


def to_object_id(id_str: str) -> ObjectId:
    try:
        return ObjectId(id_str)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid ID format")


def serialize(doc: dict):
    if not doc:
        return doc
    doc["id"] = str(doc.pop("_id"))
    # Convert datetimes to isoformat if present
    for k, v in list(doc.items()):
        if isinstance(v, datetime):
            doc[k] = v.isoformat()
    return doc


@app.get("/")
def read_root():
    return {"message": "Hospital Management System API is running"}


@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set",
        "database_name": "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set",
        "connection_status": "Not Connected",
        "collections": []
    }

    try:
        if db is not None:
            response["database"] = "✅ Available"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["connection_status"] = "Connected"
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️ Connected but Error: {str(e)[:80]}"
        else:
            response["database"] = "⚠️ Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:80]}"

    return response


# Admin endpoints (basic lists/creation)
@app.post("/api/users", response_model=dict)
def create_user(user: User):
    user_id = create_document("user", user)
    return {"id": user_id}


@app.get("/api/users", response_model=List[dict])
def list_users():
    docs = get_documents("user")
    return [serialize(d) for d in docs]


@app.post("/api/doctors", response_model=dict)
def create_doctor(doctor: Doctor):
    # Ensure referenced user exists
    if db["user"].find_one({"_id": to_object_id(doctor.user_id)}) is None:
        raise HTTPException(status_code=404, detail="User not found")
    doctor_id = create_document("doctor", doctor)
    return {"id": doctor_id}


@app.get("/api/doctors", response_model=List[dict])
def list_doctors():
    docs = get_documents("doctor")
    return [serialize(d) for d in docs]


@app.post("/api/patients", response_model=dict)
def create_patient(patient: Patient):
    if db["user"].find_one({"_id": to_object_id(patient.user_id)}) is None:
        raise HTTPException(status_code=404, detail="User not found")
    patient_id = create_document("patient", patient)
    return {"id": patient_id}


@app.get("/api/patients", response_model=List[dict])
def list_patients():
    docs = get_documents("patient")
    return [serialize(d) for d in docs]


# Appointment workflows
@app.post("/api/appointments", response_model=dict)
def create_appointment(appt: Appointment):
    if db["patient"].find_one({"_id": to_object_id(appt.patient_id)}) is None:
        raise HTTPException(status_code=404, detail="Patient not found")
    if db["doctor"].find_one({"_id": to_object_id(appt.doctor_id)}) is None:
        raise HTTPException(status_code=404, detail="Doctor not found")
    appt_id = create_document("appointment", appt)
    return {"id": appt_id}


@app.get("/api/appointments", response_model=List[dict])
def list_appointments(patient_id: Optional[str] = None, doctor_id: Optional[str] = None, status: Optional[str] = None):
    query = {}
    if patient_id:
        query["patient_id"] = patient_id
    if doctor_id:
        query["doctor_id"] = doctor_id
    if status:
        query["status"] = status
    docs = get_documents("appointment", query)
    return [serialize(d) for d in docs]


class AppointmentStatusUpdate(BaseModel):
    status: str


@app.patch("/api/appointments/{appointment_id}")
def update_appointment_status(appointment_id: str, body: AppointmentStatusUpdate):
    oid = to_object_id(appointment_id)
    res = db["appointment"].update_one({"_id": oid}, {"$set": {"status": body.status, "updated_at": datetime.utcnow()}})
    if res.matched_count == 0:
        raise HTTPException(status_code=404, detail="Appointment not found")
    doc = db["appointment"].find_one({"_id": oid})
    return serialize(doc)


# Prescription (doctor action)
@app.post("/api/prescriptions", response_model=dict)
def create_prescription(p: Prescription):
    if db["appointment"].find_one({"_id": to_object_id(p.appointment_id)}) is None:
        raise HTTPException(status_code=404, detail="Appointment not found")
    pid = create_document("prescription", p)
    return {"id": pid}


@app.get("/api/prescriptions", response_model=List[dict])
def list_prescriptions(appointment_id: Optional[str] = None):
    q = {"appointment_id": appointment_id} if appointment_id else {}
    docs = get_documents("prescription", q)
    return [serialize(d) for d in docs]


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
