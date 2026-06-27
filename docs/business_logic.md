## 🔄 Business Workflow & Financial Matrix

The system operates on an **Upfront Payment Policy** for online bookings, combined with strict time-window rules to protect the clinic from lost revenue due to last-minute cancellations or un-utilized time slots.

---

### ⏳ 1. Booking & Session Expiration Rules (Timeline Contracts)

To prevent data inconsistency and safely automate slot releases, the life-span of any Stripe checkout session (`expires_at`) is dynamically computed at creation using the following priority:

$$\text{expires\_at} = \min(\text{now} + 24\text{ hours}, \text{slot.start} - 1\text{ hour})$$

#### Online Booking Scenarios (Patients):
* **Advanced Booking (> 24 hours before start):** The patient has exactly **24 hours** to complete the payment. If unpaid, the Stripe session expires, triggers a webhook, and the backend automatically cancels the appointment to free up the slot.
* **Next-Day Booking (Between 24 and 2 hours before start):** The checkout session will expire **exactly 1 hour before the appointment starts**. This ensures that the clinic has a 1-hour buffer to re-monetize the slot if the initial patient fails to pay.
* **Urgent Booking (< 1 hour before start):** Online self-booking is **disabled** via serializer validation. The patient is instructed to call the reception.

#### Walk-in / Phone Booking Scenarios (Clinic Staff):
* When a booking is made by a receptionist (`request.user.is_staff = True`), the 1-hour restriction is bypassed. 
* The system **skips external Stripe session generation**. The receptionist captures the payment offline (Cash/POS Terminal), and the system immediately creates a locally confirmed `PAID` transaction ledger.

---

### 💰 2. Post-Payment Cancellation & Refund Matrix

Once an appointment is successfully funded (`Payment Status: PAID`), manual cancellations via `POST: appointments/<id>/cancel/` or client-side absences trigger a tiered refund sequence evaluated against the active database context:

| Time until Appointment Start | Initiator | Financial Consequence | System Action |
| :--- | :--- | :--- | :--- |
| **> 3 Hours** | Patient / Staff | **100% Flexible Refund** | Triggers full refund via Stripe API. Sets appointment to `CANCELLED`. |
| **Between 3 Hours and 1 Hour** | Patient | **Late Cancellation Fee Withheld** | Triggers partial refund via Stripe API (Withholds a **$5 penalty**). |
| **Between 3 Hours and 1 Hour** | Staff (Admin) | **Exempted Full Refund** | Admins bypass penalties. Triggers 100% refund despite the tight window. |
| **< 1 Hour** | Patient / Staff | **100% Penalty No-Refund** | No refund is issued. The clinic keeps the full amount. Slot becomes `CANCELLED`. |
| **Appointment Time Past** | Automated Job | **No-Show Fee Application** | Celery Beat marks un-attended records as `NO_SHOW`. 100% of the funds are kept. |

---
--

### 📡 3. Webhook Architecture (Asynchronous Synchronization)

1. **`checkout.session.completed`**: Dispatched by Stripe immediately upon payment success. Changes internal payment status to `PAID` and unlocks the verified appointment status.
2. **`checkout.session.expired`**: Dispatched by Stripe when the dynamic `expires_at` threshold is hit without payment activity. The backend catches this, updates the local payment to `EXPIRED`, updates the appointment to `CANCELLED`, and automatically releases the `DoctorSlot` back into the public catalog.









The diagram below illustrates the end-to-end integration between the Patient, Clinic API Backend, Stripe Gateway, 
and the Admin Telegram Notification Service during a standard booking and payment sequence.



### 💳 Appointment Booking & Stripe Payment Workflow

The system enforces an "Upfront Payment" architectural pattern for regular patients, while allowing flexibility 
for clinic staff (admins) booking via phone.

#### Step 1: Appointment Creation Request (The Trigger)
* **Action:** A patient selects a doctor and an available time slot via the frontend application, or a receptionist 
takes a booking over the phone. In both scenarios, an HTTP client dispatches a request to the backend:
  `POST /clinic/appointments/`
* **Payload Structure (Frontend/Client App):**
  ```json
  {
    "slot": 12,
    "frontend_success_url": "[https://my-clinic.com/payment/success](https://my-clinic.com/payment/success)",
    "frontend_cancel_url": "[https://my-clinic.com/payment/cancel](https://my-clinic.com/payment/cancel)"
  }
  

Note: Regular patients omit the patient field (it defaults to request.user). Admin staff must explicitly pass the "patient": <id> field.
Step 2: Automatic Internal Verification & Payment Initialization

    Backend Processing:

        The AppointmentSerializer validates that the selected DoctorSlot is not expired and is not already booked.

        The serializer calculates the exact financial figures dynamically, extracting doctor__price_per_visit.

        Inside a database transaction.atomic() block, the system creates the Appointment instance and caches 

        the frontend_success_url and frontend_cancel_url in the context.

        The view invokes the polymorphic payment subsystem:

        StripePayment(appointment, frontend_success_url=..., frontend_cancel_url=...).create_payment()

        The service logs a local Payment transaction record as PENDING, connects to the Stripe API, and provisions a 

        unique stripe.checkout.Session.

        The backend appends ?payment_id=<id> as a tracking token to the target redirect endpoints.

Step 3: API Response & Frontend Redirect

    Response: The endpoint returns an HTTP 201 Created status with the complete serialized appointment structure 

    enhanced with a transitional URL:


```json
{
  "id": 42,
  "slot": 12,
  "price": "50.00",
  "status": "BOOKED",
  "checkout_url": "[https://checkout.stripe.com/c/pay/cs_test](https://checkout.stripe.com/c/pay/cs_test)_..."
}
```

Client Handling: If the booking is initialized by a client app, the frontend immediately redirects the patient’s  
browser to the provided checkout_url.

    Staff Bypass: If the request is made by a receptionist (request.user.is_staff), the checkout_url returns null,

    and the reservation completes without a Stripe redirect.

Step 4: Asynchronous Reminders & Expiration Loops

    Notification Dispatch: Immediately upon payment schema registration, a worker triggers a non-blocking background notification task.

    # todo (Celery & Telegram Integration):

        Implement send_telegram_notification_task.delay(appointment_id=..., checkout_url=...) triggered from the Viewset create() method.

        The custom Telegram Bot must ping the patient/staff channel with booking confirmations and the active payment link, reminding them that payment must be finalized within 24 hours.

🔀 Settlement Handlers (Stripe Callbacks)

Once the user completes or interacts with the Stripe Checkout layout, the system processes two possible outcomes.
🟢 Outcome A: Successful Settlement (Payment Captured)

    The Webhook Pathway (Primary Data Integrity):

        Stripe dispatches an asynchronous cryptographic HTTP POST event directly to the server's webhook listener:
        POST /payments/webhook/

        The backend validates the integrity of the request payload using stripe.Webhook.construct_event and the endpoint signature secret.

        If the payload type evaluates to checkout.session.completed, the system executes:
        AppointmentPayment.complete_payment(session_id)

        This modifies the local Payment status column to PAID in the database.

    The Synchronous Web Redirect Pathway (User Experience):

        Simultaneously, Stripe returns the user's web browser back to the application's verification endpoint:
        GET /payments/success/?payment_id=42

        Race Condition Mitigation Logic: * The success_view inspects the local database for payment status.

            Scenario 1 (Ideal): Database already marks status as PAID ➡️ Backend immediately responds with {"status": "PAID", "message": "Оплата успішна, візит підтверджено"}.

            Scenario 2 (Webhook Latency): Database status is still PENDING ➡️ The view instantly triggers a live fallback HTTP fetch via the Stripe SDK: stripe.checkout.Session.retrieve(session_id). If Stripe declares it paid, the view updates the local database dynamically on the spot and clears the user screen safely.

        # todo: Write tests and final code lines for the success_view verification route.

🔴 Outcome B: Payment Abandoned or Paused

    The Cancel Pathway:

        If the patient hits the "Cancel and return to merchant" toggle inside the Stripe console, 

        Stripe sends their browser to the designated endpoint:

        GET /payments/cancel/?payment_id=42

        The backend responds with a custom notification message:
        {"status": "PENDING", "message": "Payment paused. You can pay later within 24 hours."}

    State Resolution:

        The internal database state for the Payment tracking item remains PENDING.

        The patient retains a 24-hour window to re-open the initial checkout_url extracted from their 
        profile history to complete the reservation before automated cleanup routines evict the slot.

        # todo: Build out the corresponding cancel_view route logic.