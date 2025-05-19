import frappe
import secrets
from datetime import timedelta
from frappe.utils import now_datetime

def generate_checkin_token():
    # Expire previous tokens
    frappe.db.set_value("Check-In Token", {"is_active": 1}, "is_active", 0)

    token = secrets.token_urlsafe(16)
    reference_url = f"/checkin/member?token={token}"
    expiry = now_datetime() + timedelta(minutes=5)
    frappe.logger().info(f"[DEBUG] Token expiry set to: {expiry}")

    
    # Create and insert the document
    doc = frappe.get_doc({
        "doctype": "Check-In Token",
        "token": token,
        "expiry_time": expiry,
        "is_active": 1,
        "reference_url": reference_url
    })
    doc.insert(ignore_permissions=True)
    doc.submit()

    frappe.db.commit()
    frappe.logger().info(f"Generated and submitted token: {token}")
