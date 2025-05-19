import frappe
import frappe.sessions

def get_context(context):
    token = frappe.form_dict.token
    doc = frappe.get_all("Check-In Token", filters={
        "token": token,
        "is_active": 1,
        "expiry_time": [">", frappe.utils.now_datetime()]
    }, limit=1)

    if not doc:
        context.invalid_token = True
        return context

    context.valid_token = True
    context.token = token
    context.csrf_token = frappe.sessions.get_csrf_token()  # ← ✅ Add this line
    return context
