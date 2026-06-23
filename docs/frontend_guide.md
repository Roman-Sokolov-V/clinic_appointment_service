# 💻 Frontend & API Integration Guide

Since this project features a browsable REST API interface, any decoupled frontend client (Web application, Mobile app, or Telegram bot microservice) must implement the specific routing, authorization, and polling mechanics detailed below to ensure a smooth, race-condition-free user experience.
## 🔑 1. Authorization (DRF Simple JWT)

The backend utilizes the JSON Web Token (JWT) mechanism with strict Token Rotation and active Blacklisting.

    ACCESS_TOKEN_LIFETIME: 60 minutes.

    REFRESH_TOKEN_LIFETIME: 7 days.

### 🔄 Important Rotation Rule (Rotate & Blacklist)

On the backend, ROTATE_REFRESH_TOKENS: True and BLACKLIST_AFTER_ROTATION: True parameters are activated.

    ⚠️ Critical for Client Apps: Whenever a client sends a request to update
    an expired token via /api/users/token/refresh/, the backend returns a NEW PAIR:
    both a new access token and a new refresh token.
    The old refresh token is automatically burned and blacklisted. 
    The client must immediately overwrite both tokens in its persistent storage 
    (Local Storage / Secure Store / Redis). If the client attempts to reuse a 
    burned refresh token, the server rejects it with a 401 Unauthorized status.

## 📡 2. API Endpoints Reference

Base URL: http://<your-domain-or-localhost>/api/
### 📡 Complete API Endpoints Reference

| Endpoint | Method | Description | Access Level |
| :--- | :---: | :--- | :--- |
| **🔐 Users Service** | | | |
| `/api/users/` | `POST` | Register a new user (patient) | Public |
| `/api/users/token/` | `POST` | Login (obtain initial JWT access/refresh token pair) | Public |
| `/api/users/token/refresh/` | `POST` | Refresh an expired access token using the refresh token | Public |
| `/api/users/me/` | `GET` | Retrieve current user profile info | Authorized |
| `/api/users/me/` | `PUT/PATCH` | Update current user profile info | Authorized |
| **🗂️ Specializations Service** | | | |
| `/api/specializations/` | `POST` | Add a new medical specialization | Staff Only |
| `/api/specializations/` | `GET` | Get a list of all specializations (paginated) | Authorized |
| `/api/specializations/<id>/` | `GET` | Get detailed information about a specific specialization | Authorized |
| `/api/specializations/<id>/` | `PUT/PATCH` | Update specialization metadata | Staff Only |
| `/api/specializations/<id>/` | `DELETE` | Delete a specialization | Staff Only |
| **🩺 Doctors & Slots Service** | | | |
| `/api/doctors/` | `POST` | Add a new doctor profile | Staff Only |
| `/api/doctors/` | `GET` | Get filtered list of doctors (e.g., `?specialization=id_or_code`) | Authorized |
| `/api/doctors/<id>/` | `GET` | Get detailed profile of a specific doctor | Authorized |
| `/api/doctors/<id>/` | `PUT/PATCH` | Update doctor profile details | Staff Only |
| `/api/doctors/<id>/` | `DELETE` | Delete a doctor profile | Staff Only |
| `/api/doctors/<id>/slots/` | `POST` | Bulk create time slots for a specific doctor | Staff Only |
| `/api/doctors/<id>/slots/` | `GET` | List doctor's slots (supports `?from=`, `?to=`, `?available_only=true/false`) | Authorized |
| `/api/slots/<id>/` | `GET` | Get specific slot breakdown | Authorized |
| `/api/slots/<id>/` | `DELETE` | Delete a slot (allowed only if no active appointment exists) | Staff Only |
| **📅 Appointments Service** | | | |
| `/api/appointments/` | `POST` | Book an appointment (fails if slot is already `BOOKED`) | Authorized |
| `/api/appointments/` | `GET` | List appointments (supports `?patient_id=`, `?doctor_id=`, `?status=`, `?from=`, `?to=`) | Authorized |
| `/api/appointments/<id>/` | `GET` | Get explicit appointment details | Authorized |
| `/api/appointments/<id>/cancel/` | `POST` | Cancel appointment (late-cancel may dynamically trigger a fee) | Authorized |
| `/api/appointments/<id>/complete/` | `POST` | Mark appointment status as completed | Staff Only |
| `/api/appointments/<id>/no-show/` | `POST` | Mark patient as `NO_SHOW` (manually or via automated scheduler) | Staff Only |
| **💳 Payments Service (Stripe)** | | | |
| `/api/payments/success/` | `GET` | Callback validation route to verify successful payment (`?payment_id=`) | Authorized |
| `/api/payments/cancel/` | `GET` | Stub view displaying paused transaction state to browser clients | Authorized |


📥 Request Format: /api/users/token/ (Login)  
JSON

{
    "username": "user_login",
    "password": "user_password"
}

Response (200 OK):
JSON

{
    "access": "eyJhbGciOiJIUzI1NiIsIn...",
    "refresh": "eyJhbGciOiJIUzI1NiIsIn..."
}

🔄 Request Format: /api/users/token/refresh/
JSON

{
    "refresh": "current_refresh_token_here"
}

Response (200 OK):
JSON

{
    "access": "new_access_token_here",
    "refresh": "new_refresh_token_here"
}

## 📋 3. Working with Pagination

Lists of specializations, doctors, and slots use native Limit/Offset pagination.
When querying a paginated endpoint (e.g., /api/specializations/?limit=10&offset=0), the server responds with the following structure:
JSON

{
    "count": 42,
    "next": "http://localhost:8000/api/specializations/?limit=10&offset=10",
    "previous": null,
    "results": [
        { "id": 1, "name": "Cardiologist", "code": "cardiology" },
        ...
    ]
}

    Rule for Clients: Do not hardcode custom page calculation calculations. If the "next" field is not null, the client should simply execute the next background query directly to that returned URL string, or cleanly extract the updated limit and offset query parameters.

## 📅 4. Slot Selection and Data Privacy

When querying /api/slots/?doctor_id={id}, the backend computes a dynamic schedule matrix.

    Privacy Constraint: Regular users (patients/customers) only see free (unreserved) slots. Booked or fully reserved slots are automatically omitted from the HTTP response to maintain strict healthcare privacy standards.

    The complete visibility matrix (showing both available, booked, and blocked intervals) is strictly accessible by clinic administrators or staff members (IsAdminUser / IsStaff).

## 💳 5. Checkout & Stripe Integration Workflow

When a patient books an appointment, the frontend client handles the checkout presentation layer and payment routing dynamically.
📥 1. Dispatching the Booking Request

When initiating a POST /api/appointments/ request, the frontend must pass the selected slot, payment method, and two absolute callback URLs where the user should be returned after interacting with the Stripe checkout template:
JSON

{
  "slot_id": 142,
  "payment_method": "stripe",
  "frontend_success_url": "https://clinic.my-app.com/booking/success",
  "frontend_cancel_url": "https://clinic.my-app.com/booking/cancel"
}

(Available options for payment_method are "stripe" or "cash").
📤 2. Extracting Checkout Metadata

Response (201 Created):
JSON

{
    "id": 55,
    "slot_id": 142,
    "status": "pending",
    "checkout_url": "https://checkout.stripe.com/c/pay/cs_test_...",
    "window_fee": 120,
    "percent_fee": 20
}

    If payment_method == "stripe": The frontend must intercept checkout_url and immediately redirect the user's browser (or open an in-app Webview component) to that exact external destination.

    Reservation Expiry: The patient has a strict 24-hour window to complete the payment session. If payment fails or clears the expiration boundary, background Celery workers clean up the stale instance and release the slot.

    Cancellation Rules: The API response yields protection metrics: Cancellation occurring earlier than window_fee minutes triggers an automated 100% refund. Cancellations made inside the window_fee buffer incur a percent_fee penalty.

## 🔄 6. Redirect Handling & Client-Side Polling

Because Stripe webhooks (backend database update) and user browser redirects (frontend landing) operate completely asynchronously, a race condition can occur. The user may land back on the frontend app before the webhook processing is finished.
🟢 Handling Success Loops (frontend_success_url)

    Intercept Tracking Parameters: Once payment is cleared, Stripe returns the patient to your specified frontend_success_url. The backend automatically appends the relational payment ID as a query tracker:
    https://clinic.my-app.com/booking/success?payment_id=42

    Execute the Polling Loop: The frontend must extract payment_id and execute background GET validation calls to:
    GET /api/payments/success/?payment_id=<extracted_id>

Polling State Rules Table:
Backend Status Response	HTTP Status	Frontend Action	UX Display
{"status": "PAID"}	200 OK	Terminate polling loop immediately.	"Payment confirmed! Your appointment is secured."
{"status": "PENDING"}	200 OK	Maintain polling. Wait 2 seconds, then execute next request.	Display a loading spinner: "Verifying transaction with your bank..."
Any Error Code	400 / 404	Terminate polling loop immediately.	Display system error layout.

    Fallback Boundary Constraints: Attempt this polling verification a maximum of 5 times (approx. 10 seconds aggregate). If it remains PENDING after 5 cycles, break the loop and render a safe fallback screen: "Your payment is currently being processed by your banking institution. We will dispatch a confirmation notice via Telegram as soon as it clears. You can safely close this page."

🔴 Handling Abandoned Payments (frontend_cancel_url)

If the patient manually terminates the payment phase or clicks "Cancel and return to merchant" inside the Stripe view, Stripe routes the user immediately back to your designated frontend_cancel_url.

    Frontend Responsibility: The client app manages the UI state entirely local-side. No API verification calls are needed since the transaction state safely remains PENDING on the backend.

    UX Presentation: Render a local error panel: "You have paused or cancelled the payment sequence. You can still complete your booking within the next 24 hours via your appointment profile history."

    ⚠️ Development Sandbox Note: If manual endpoint testing is performed through the native DRF Browsable API interface without an external client UI attached, the backend provides a fallback route at GET /api/payments/cancel/?payment_id=<id>. This acts purely as a mock sandbox view to print transaction diagnostics in your browser, returning a 200 OK status with diagnostic metadata. In production, Stripe routes directly to the detached client instance.