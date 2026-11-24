import secrets
from datetime import timedelta

import frappe
from frappe import _
from frappe.rate_limiter import rate_limit
from frappe.utils import now_datetime

OTP_MINUTES = 5


# Members check in without an account, so this stays open to guests; the QR token, the
# per-member rate limit and the one-time code sent to the member guard it.
# nosemgrep: frappe-semgrep-rules.rules.security.guest-whitelisted-method
@frappe.whitelist(allow_guest=True, methods=["POST"])
@rate_limit(key="member_id", limit=3, seconds=OTP_MINUTES * 60, ip_based=False)
def send_otp(token: str | None = None, member_id: str | None = None):
	"""Store a one-time code for a member checking in with a valid QR token and send it to them."""
	token, member_id = (token or "").strip(), (member_id or "").strip()
	if not token or not member_id:
		frappe.throw(_("Missing token or member ID"))

	active_token = {"token": token, "is_active": 1, "expiry_time": [">", now_datetime()]}
	if not frappe.db.exists("Check-In Token", active_token):
		frappe.throw(_("Invalid or expired token"))

	otp = f"{secrets.randbelow(10**6):06d}"
	frappe.get_doc(
		{
			"doctype": "OTP Record",
			"token": token,
			"member_id": member_id,
			"otp": otp,
			"expires_at": now_datetime() + timedelta(minutes=OTP_MINUTES),
			"is_verified": 0,
		}
	).insert(ignore_permissions=True)
	deliver_otp(member_id, otp)
	return {"message": _("OTP sent")}


def deliver_otp(member_id, otp):
	"""Send the code to the member. No channel is set up yet, so check-in stops here."""
	frappe.throw(_("OTP delivery is not set up yet. Ask the administrator to check you in."))
