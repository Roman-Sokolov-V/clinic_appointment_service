


 «https://accounts.google.com/o/oauth2/auth в браузер і постман використовується для редіректу в гугл і в ньому додається Client_ID»

        Абсолютно вірно. Це стартова точка (URL авторизації Google), куди ми відправляємо користувача разом із його Client_ID.

    «гугл після авторизації юзера повертає код на Callback URL (запит був з постмен)»

        Абсолютно вірно. Якщо ми налаштовували автомат у Postman, Google повертає код на Callback URL самого Постмана (наприклад, https://oauth.pstmn.io/v1/callback), і Постман сам його ловить.

    «або http://127.0.0.1:8000/users/auth/google/ (запит був з браузер)»

        Ось тут маленький нюанс! Google повертає код не на ендпоінт /users/auth/google/.

        Як насправді: Google повертає код на той Callback URL, який прописаний для твоєї програми (на фронтенд, або на спеціальний callback-ендпоінт allauth, наприклад, http://127.0.0.1:8000/accounts/google/login/callback/). Браузер завантажує цю сторінку і бачить код в адресному рядку.

        А вже потім фронтенд (або скрипт) бере цей код і робить окремий, новий POST-запит на твій ендпоінт http://127.0.0.1:8000/users/auth/google/.

1. Дія: Пацієнт обрав час, доктора і створив запис через додаток, або по телефону але в обох випадках це запит на POST /clinic/appointments
2. Автоматично (backend)створюється payment з session.id session.url 
(StripePayment(appointment).create_payment()) , повертаєтья відповідь   (на POST /clinic/appointments)  з session.url
і якщо цей запит зробив додаток пацієнта то фронтенд редиректить його на session.url 

(або можна на бекенді якщо request.user.is_staff - status 201  а якщо ні то редірект на  session.url - але ми так робити не будемо)

3. Відправляється нотифікація - Telegram користувачу про створення appointment з просьбою оплатити протягом 24-годин,
з посиланням на Stripe  сторінку оплати - session.url,
# todo написати телеграм бот
# todo реалізувати відправку месседжа (напевно через Celery, виклик таски після створення payment в create вьюсету appointment)
4. Користувач йде за посиланням session.url і оплачує
5.1 Коли оплата пройшла Stripe відправляє на ендпоінт вебхука подію з типом 'checkout.session.completed'
бекенд - отримавши робить StripePayment.complete_payment(session.id) - міняє статус оплати на PAID, 
Одночасно Stripe редиректить користувача на ендпоінт success/?session_id=cs_test_.... 
де бекенд перевіряє що  payment.status == 'Paid' і відповідає {"message": "Оплата успішна, візит підтверджено"}
Якщо статус досі PENDING (вебхук запізнюється) ➡️ твоя View сама робить швидкий запит в Stripe: stripe.checkout.Session.retrieve(session_id).
# todo написати вью для success/
5.2  Якщо користувач натиснув кнопку "Скасувати і повернутися в магазин" на сторінці Stripe. 
 його редиректить на cancel/ бекенд повертає {"message": "Payment paused. You can pay later within 24 hours."}
Статус платежу в базі залишається PENDING. У юзера є 24 години, щоб перейти за тим самим посиланням ще раз.
# todo написати вью для cancel/









## 🔄 Core Business Workflows & Data Flow



## 🔄 Final Business Workflow & Financial Matrix

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





## 💳 Stripe Integration & Webhook Setup

This project uses Stripe for handling consultation fees and payments. To make payments and webhooks work in
your local development environment, follow this complete guide.

---

### 1. Stripe Account Registration
1. Go to the [Stripe Registration Page](https://dashboard.stripe.com/register).
2. Create an account and verify your email.
3. Open your Stripe Dashboard and ensure you are in **Sandbox Mode** (toggle switch in the top right corner). 
   > ⚠️ **Never use Production (Live) keys for local development!**

---

### 2. Obtain API Keys
Navigate to **Developers** -> **API keys** tab in your Stripe Dashboard. Copy the following keys and add them to your `.env` file:

* **Publishable key** (starts with `pk_test_...`) -> Set as `STRIPE_PUBLISHABLE_KEY`
* **Secret key** (starts with `sk_test_...`) -> Set as `STRIPE_SECRET_KEY`

---

### 3. Install Stripe CLI (Linux / Ubuntu)
Since your local server runs on `localhost`, Stripe cannot send webhooks to your machine directly. You need the 
**Stripe CLI** to create a secure tunnel.

Go to https://docs.stripe.com/stripe-cli/install and follow instructions for your OS 

### 4. Link Stripe CLI to Your Account

Before running the tunnel, you must authorize the CLI tool:  
1. Run the login command:  
    ```Bash
    stripe login
    ```
2. The terminal will output a unique pairing code and an authentication URL.
3. Press Enter to open your browser (or copy-paste the link manually), log into your Stripe Dashboard, and confirm the pairing code.
4. Once authorized, the terminal will display ✓ Authenticated successfully!.

### 5. Start Webhook Forwarding & Get Endpoint Secret  

To start forwarding Stripe events to your local Django application and get your webhook signing secret:

1. Run the listener command (make sure your Django port matches):
   ```Bash
   stripe listen --forward-to localhost:8000/clinic/payments/webhook/
   ```
2. As soon as the command starts, look for the following line in the terminal output:

    Ready! Your webhook signing secret is whsec_...
3. Copy this whsec_... key and add it to your .env file:
```
STRIPE_WEBHOOK_SECRET=whsec_your_copied_secret_here
```
   ⚠️ Important Notes:

    Keep the stripe listen terminal tab open while testing payments. If you close it, webhooks will stop arriving.

    Every time you restart the stripe listen session, a new whsec_ key might be generated. Always double-check that your 
    .env matches the current terminal output.  

    STRIPE_WEBHOOK_SECRET will be expired in 90 days







## 💻 Frontend Integration Guide

Since this project is a browsable API, any frontend client (Web application, Mobile app, or Telegram bot) must implement specific routing and polling mechanics to ensure a smooth user experience during the payment flow.

### 🔄 Dynamic Redirects & Polling Workflow

When a patient books an appointment, the frontend team is responsible for managing the redirection to Stripe and verifying the payment status upon return.






#### 1. Dispatching the Booking Request
When initiating a `POST /clinic/appointments/` request, the frontend **must** generate and inject two absolute URLs where the user should be returned after interacting with Stripe:
* `frontend_success_url`: The landing page on the frontend for successful or completed checkouts.
* `frontend_cancel_url`: The landing page on the frontend if the user abandons the checkout.

*Example Payload:*
```json
{
  "slot": 15,
  "frontend_success_url": "[https://clinic.my-app.com/booking/success](https://clinic.my-app.com/booking/success)",
  "frontend_cancel_url": "[https://clinic.my-app.com/booking/cancel](https://clinic.my-app.com/booking/cancel)"
}
```

Upon receiving the response, the frontend must extract the checkout_url and redirect the user's browser (or open an in-app Webview) to that exact link.
2. Handling the Return to frontend_success_url

Once the payment is processed, Stripe redirects the patient back to your specified frontend_success_url.
The backend automatically appends a tracking token as a query parameter to this URL:
?payment_id=<id>

    Example Destination: https://clinic.my-app.com/booking/success?payment_id=42

3. Implementing the Client-Side Polling (Race Condition Protection)

Because the Stripe Webhook (which updates the database) and the user's browser redirect happen asynchronously, the frontend must not assume the database is updated instantly.

The frontend should implement the following validation loop on the success landing page:

    Intercept the Token: Extract the payment_id value from the active browser URL parameters.

    Ping the Backend: Make a background GET request to the backend validation route:
    GET /payments/success/?payment_id=<extracted_id>

    Evaluate State & Retry (Polling Loop):

        Case 200 OK ({"status": "PAID"}): Stop the loop, hide any loading animations, and display a success screen ("Payment confirmed! Your appointment is successfully booked.").

        Case 200 OK ({"status": "PENDING"}): Do not fail. Show a loading spinner with a message ("Verifying your payment with the bank..."). Wait for 2 seconds, then repeat the GET request.

    Fallback & Timeout Limits:

        The frontend should attempt this verification a maximum of 5 times (approx. 10 seconds total).

        If after 5 attempts the status remains PENDING, break the loop and notify the user with an intermediate status message:
        "Your payment is currently being processed by the financial institution. We will text you a confirmation via Telegram as soon as it clears. You can safely close this page."

        If the backend returns a 404 Not Found or 400 Bad Request, immediately terminate the loop and show an error screen.

#### 🔴 Outcome B: Payment Abandoned or Paused

1. **The Cancel Pathway (Development Backend Stub):**
   * If the patient hits the *"Cancel and return to merchant"* toggle inside the Stripe checkout console, Stripe returns their browser to the designated endpoint:
     `GET /payments/cancel/?payment_id=42`
   * **Browsable API Optimization:** Since this project runs without a separate frontend client, this view acts as a temporary backend **stub**. It prevents a `404 Not Found` error in the browser during manual testing and explicitly displays the transaction state.
   * The backend responds with an informative JSON payload:
     ```json
     {
       "status": "PENDING",
       "message": "Payment was paused or cancelled by the user. The slot is held for 24 hours.",
       "hint": "This is a backend stub view. In production, Stripe will redirect directly to the frontend application."
     }
     ```

2. **State Resolution:**
   * The internal database state for the `Payment` tracking item remains `PENDING`. 
   * The patient retains a **24-hour window** to re-open the initial `checkout_url` extracted from their profile history to complete the reservation before automated cleanup routines evict the slot (`checkout.session.expired` webhook).

---

## 💻 Frontend Integration Guide

Since this project features a browsable API interface, any decoupled frontend client (Web application, Mobile app, or Telegram bot) must implement specific routing and polling mechanics to ensure a smooth user experience.

### 🔀 Redirection Contracts & URL Handlers

When a patient initiates a booking via `POST /clinic/appointments/`, the frontend application is responsible for passing its own absolute callback paths (`frontend_success_url` and `frontend_cancel_url`).

#### 🟢 1. Handling Success (`frontend_success_url`)
Stripe will return the user here after a successful capture. The backend automatically appends `?payment_id=<id>` to this URL.

* **Frontend Responsibility:** The frontend **must intercept** the `payment_id` parameter and run a background polling loop against the backend validation endpoint (`GET /payments/success/?payment_id=...`). 
* **Polling Logic:** If the backend returns `{"status": "PENDING"}`, the frontend should show a loading spinner and retry every 2 seconds (up to 5 times) until the webhook updates the database to `PAID`.

#### 🔴 2. Handling Cancellations (`frontend_cancel_url`)
If the user clicks "Cancel" on the Stripe layout, Stripe redirects the browser **directly back to the frontend application** (e.g., `https://my-clinic.com/booking/cancel`).

* **⚠️ Production Architecture Note:** In a production environment with a live frontend, the backend `payments/cancel/` endpoint is **completely redundant and should be removed**. 
* **Frontend Responsibility:** The frontend handles the cancellation state entirely client-side. Since the payment status in the database safely remains `PENDING`, the frontend just renders a local page: *"You have cancelled the payment process. You can still pay for this appointment within the next 24 hours via your profile history."* layout without dispatching any API calls to the backend.