import frappe
from frappe import _
from frappe.rate_limiter import rate_limit
from frappe.utils import now_datetime

from cupstone.attendance.api.send_otp import OTP_MINUTES


# Open to guests for the same reason as send_otp. The per-member limit stops a six-digit
# code being guessed from many addresses within its lifetime.
# nosemgrep: frappe-semgrep-rules.rules.security.guest-whitelisted-method
@frappe.whitelist(allow_guest=True, methods=["POST"])
@rate_limit(key="member_id", limit=5, seconds=OTP_MINUTES * 60, ip_based=False)
def verify_otp(token: str | None = None, member_id: str | None = None, otp: str | None = None):
	"""Check a member in when their code matches an unused, unexpired one."""
	token, member_id, otp = (token or "").strip(), (member_id or "").strip(), (otp or "").strip()
	if not token or not member_id or not otp:
		frappe.throw(_("Missing token, member ID, or OTP"))

	name = frappe.db.get_value(
		"OTP Record",
		{
			"token": token,
			"member_id": member_id,
			"otp": otp,
			"is_verified": 0,
			"expires_at": [">", now_datetime()],
		},
	)
	if not name:
		frappe.throw(_("Invalid or expired OTP"))

	otp_record = frappe.get_doc("OTP Record", name)
	otp_record.is_verified = 1
	otp_record.save(ignore_permissions=True)

	log = frappe.get_doc(
		{
			"doctype": "Attendance Log",
			"member_id": member_id,
			"token": token,
			"otp_record": name,
			"check_in_time": now_datetime(),
		}
	)
	log.insert(ignore_permissions=True)
	log.submit()
	return {"message": _("Check-in successful"), "member_id": member_id}
