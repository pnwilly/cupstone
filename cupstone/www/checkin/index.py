import frappe
import qrcode
import io
import base64

def get_context(context):
    # Get latest token
    doc = frappe.get_all(
        "Check-In Token",
        filters={"is_active": 1},
        fields=["reference_url", "expiry_time"],
        order_by="creation desc",
        limit=1
    )
    
    url = doc[0]["reference_url"] if doc else "/checkin/expired"
    expiry_time = doc[0]["expiry_time"] if doc else frappe.utils.now_datetime()

    # Generate QR Code
    qr = qrcode.make(frappe.utils.get_url() + url)
    buffer = io.BytesIO()
    qr.save(buffer, format="PNG")
    qr_base64 = base64.b64encode(buffer.getvalue()).decode()

    # Inject into context
    context.qr_image = f"data:image/png;base64,{qr_base64}"
    context.url = url
    context.expire_time = expiry_time.strftime('%Y-%m-%dT%H:%M:%S')
    return context
