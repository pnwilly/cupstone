import secrets
from datetime import timedelta
from unittest.mock import patch

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import now_datetime

from cupstone.attendance.api.send_otp import send_otp
from cupstone.attendance.api.verify_otp import verify_otp


class TestCheckInOTP(FrappeTestCase):
	def setUp(self):
		self.token = frappe.generate_hash(length=16)
		frappe.get_doc(
			{
				"doctype": "Check-In Token",
				"token": self.token,
				"expiry_time": now_datetime() + timedelta(minutes=5),
				"is_active": 1,
				"reference_url": f"/checkin/member?token={self.token}",
			}
		).insert(ignore_permissions=True)

	def test_send_otp_never_returns_the_code(self):
		with patch("cupstone.attendance.api.send_otp.deliver_otp") as deliver:
			response = send_otp(token=self.token, member_id="M-1")

		otp = deliver.call_args.args[1]
		self.assertEqual(len(otp), 6)
		self.assertNotIn(otp, str(response))

	def test_send_otp_stops_until_delivery_is_set_up(self):
		with self.assertRaisesRegex(frappe.ValidationError, "not set up"):
			send_otp(token=self.token, member_id="M-1")

	def test_send_otp_rejects_an_expired_token(self):
		frappe.db.set_value(
			"Check-In Token", self.token, "expiry_time", now_datetime() - timedelta(minutes=1)
		)
		with self.assertRaisesRegex(frappe.ValidationError, "Invalid or expired token"):
			send_otp(token=self.token, member_id="M-1")

	def test_matching_code_checks_the_member_in_once(self):
		otp = self._otp_record()

		verify_otp(token=self.token, member_id="M-1", otp=otp)

		self.assertTrue(
			frappe.db.exists("Attendance Log", {"member_id": "M-1", "token": self.token, "docstatus": 1})
		)
		with self.assertRaisesRegex(frappe.ValidationError, "Invalid or expired OTP"):
			verify_otp(token=self.token, member_id="M-1", otp=otp)

	def test_wrong_or_expired_code_is_rejected(self):
		otp = self._otp_record()
		with self.assertRaisesRegex(frappe.ValidationError, "Invalid or expired OTP"):
			verify_otp(token=self.token, member_id="M-1", otp=f"{(int(otp) + 1) % 10**6:06d}")

		expired = self._otp_record(minutes=-1)
		with self.assertRaisesRegex(frappe.ValidationError, "Invalid or expired OTP"):
			verify_otp(token=self.token, member_id="M-1", otp=expired)

	def _otp_record(self, minutes=5):
		otp = f"{secrets.randbelow(10**6):06d}"
		frappe.get_doc(
			{
				"doctype": "OTP Record",
				"token": self.token,
				"member_id": "M-1",
				"otp": otp,
				"expires_at": now_datetime() + timedelta(minutes=minutes),
				"is_verified": 0,
			}
		).insert(ignore_permissions=True)
		return otp
