import frappe
from frappe import _
from frappe.utils import now_datetime


@frappe.whitelist(allow_guest=True)
def verify_otp():
	# Get and sanitize input
	token = frappe.form_dict.get("token", "").strip()
	member_id = frappe.form_dict.get("member_id", "").strip()
	otp = frappe.form_dict.get("otp", "").strip()

	if not token or not member_id or not otp:
		frappe.throw(_("Missing token, member ID, or OTP"))

	# Search for matching OTP record
	otp_record = frappe.get_all(
		"OTP Record",
		filters={
			"token": token,
			"member_id": member_id,
			"otp": otp,
			"is_verified": 0,
			"expires_at": [">", now_datetime()],
		},
		limit=1,
	)

	if not otp_record:
		frappe.throw(_("Invalid or expired OTP"))

	# Mark OTP as verified
	otp_doc = frappe.get_doc("OTP Record", otp_record[0].name)
	otp_doc.is_verified = 1
	otp_doc.save(ignore_permissions=True)
	frappe.db.commit()

	# ✅ Create and submit attendance log
	log_doc = frappe.get_doc(
		{
			"doctype": "Attendance Log",
			"member_id": member_id,
			"token": token,
			"otp_record": otp_doc.name,
			"check_in_time": now_datetime(),
		}
	)
	log_doc.insert(ignore_permissions=True)
	log_doc.submit()

	return {"message": "Check-In Successful ✅", "member_id": member_id, "token": token}
