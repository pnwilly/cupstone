import random
from datetime import timedelta

import frappe
from frappe import _
from frappe.utils import now_datetime


@frappe.whitelist(allow_guest=True)
def send_otp():
	token = frappe.form_dict.get("token")
	member_id = frappe.form_dict.get("member_id")

	if not token or not member_id:
		frappe.throw(_("Missing token or member ID"))

	# Validate token
	token_doc = frappe.get_doc("Check-In Token", {"token": token, "is_active": 1})
	if not token_doc or token_doc.expiry_time < now_datetime():
		frappe.throw(_("Invalid or expired token"))

	# Generate OTP
	otp = str(random.randint(100000, 999999))
	expiry = now_datetime() + timedelta(minutes=5)

	# Create OTP Record
	frappe.get_doc(
		{
			"doctype": "OTP Record",
			"token": token_doc.name,
			"member_id": member_id,
			"otp": otp,
			"expires_at": expiry,
			"is_verified": 0,
		}
	).insert(ignore_permissions=True)

	frappe.db.commit()

	# TODO: send OTP via Email/SMS/WhatsApp here

	return {"message": f"OTP sent successfully (debug: {otp})"}
