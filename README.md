Clinic Appointment Service
Project Description:
A small private clinic books appointments by phone and writes everything  
into paper notebooks. Patients forget appointments, doctors’ schedules  
overlap, and receptionists can’t track payments or apply late-cancellation fees.
Build an online appointment management system that allows patients to   
register, browse doctors and available time slots, book appointments,  
cancel or complete visits. Payments are processed via Stripe.  
Staff receive Telegram notifications about new bookings, cancellations,  
no-shows, and successful payments.
No front-end is required, the website must be fully functional through a  
browsable API interface.
Requirements:
Functional (what the system should do):
Web-based
Manage doctors & their availability (time slots)
Manage patients (users)
Manage appointments (book, cancel, mark completed/no-show)
Display notifications
Handle payments
Non-functional (what the system should deal with):
5 concurrent users
Up to 1000 books
50k appointments/year
~30MB/year





Resources:  

### Specialization:  
- [x] Name: str (unique)  
- [x] Code: slug (unique) # stable identifier (e.g., “cardiology”)  
- [x] Description: str | null  

### Doctor:
- [x] First name: str
- [x] Last name: str
- [x] Specializations: Many-to-many to Specialization---------------------
- [x] Price per visit: decimal (USD)

### DoctorSlot:
- [x]  Doctor id: int
- [x]  Start: datetime
- [x]  End: datetime  

### User (Patient):
- [x] Email: str
- [x] First name: str
- [x] Last name: str
- [x] Password: str
- [x] Is staff: bool

### Appointment:
- [x] Doctor slot id: int
- [x] Patient id: int
- [x] Status: Enum: BOOKED | COMPLETED | CANCELLED | NO_SHOW 
(NO_SHOW — a patient who didn’t attend and didn’t cancel before the appointment time.)
- [x] Booked at: datetime
- [x] Completed at: datetime | null 
- [x] Price: decimal (USD)

### Payment:
- [x] Status: Enum: PENDING | PAID | EXPIRED
- [x] Type: Enum: CONSULTATION | CANCELLATION_FEE | NO_SHOW_FEE
- [x] Appointment id: int
- [x] Session url: Url
- [x] Session id: str
- [x] Money to pay: decimal (USD)



## Components:
### Specializations Service:
#### a. Managing catalog of medical specializations (CRUD)
#### b. API:
- [x] POST: specializations/ - add new
- [x] GET: specializations/ - get a list of specializations
- [x] GET: specializations/<id>/ - get specialization detail
- [x] PUT/PATCH: specializations/<id>/ - update specialization
- [x] DELETE: specializations/<id>/ - delete specialization

### Doctors & Slots Service:
#### Managing doctors and their time slots (CRUD)
#### API:
- [x] POST: doctors/ - add new
- [x] GET: doctors/?specialization=... - get a list (filterable by specialization id/code)
- [x] GET: doctors/<id>/ - get doctor detail
- [x]  PUT/PATCH: doctors/<id>/ - update doctor
- [x]  DELETE: doctors/<id>/ - delete doctor
- [x]  POST: doctors/<id>/slots/ - bulk create slots
- [x] GET: doctors/<id>/slots/?from=&to=&available_only=true|false
- [x] list doctor’s slots; available_only=true returns slots with no current BOOKED appointment
- [x]  GET: slots/<id>/ - get slot detail
- [x]  DELETE: slots/<id>/ - delete slot (only if no appointment exists)
### Users Service:
#### Managing authentication & user registration
#### API:
- [ ]  : users/ - register a new user
- [ ]  POST: users/token/ - get JWT tokens
- [ ]  POST: users/token/refresh/ - refresh JWT token
- [ ]  GET: users/me/ - get my profile info
- [ ]  PUT/PATCH: users/me/ - update profile info
### Appointments Service:
#### Managing patients’ appointments
#### API:
- [x]  POST: appointments/ - create appointment (fails if slot already has a BOOKED appointment)
- [x]  GET: appointments/?patient_id=...&doctor_id=...&status=...&from=&to= - list appointments
- [x]  GET: appointments/<id>/ - get appointment detail
- [x]  POST: appointments/<id>/cancel/ - cancel appointment; late-cancel may create CANCELLATION_FEE
- [x]  POST: appointments/<id>/complete/ - mark completed
- [ ]  POST: appointments/<id>/no-show/ - (staff) mark as NO_SHOW (normally set by scheduled job after slot end)
### Notifications Service (Telegram):
- [ ]  Notifications about appointment booked/cancelled/completed/no-show & successful payment
- [ ]  Runs in parallel (Django-Q or Django Celery)
- [ ]  Other services interact with it to send notifications to clinic administrators
Uses Telegram API, Telegram Chats & Bots
### Payments Service (Stripe):
#### Perform payments for consultations and policy fees through the platform
#### Interact with Stripe API using the stripe package
#### API:
- [ ]  GET: success/ - check successful stripe payment
- [ ]  GET: cancel/ - return payment paused message
- [ ]   Service (Delegated to the Front-end Team):
Front-end interface for communication with API will not be implemented here


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


## 💳 Stripe Integration & Webhook Setup

This project uses Stripe for handling consultation fees and payments. To make payments and webhooks work in your local development environment, follow this complete guide.

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
Since your local server runs on `localhost`, Stripe cannot send webhooks to your machine directly. You need the **Stripe CLI** to create a secure tunnel.

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

    Every time you restart the stripe listen session, a new whsec_ key might be generated. Always double-check that your .env matches the current terminal output.  

    STRIPE_WEBHOOK_SECRET will be expired in 90 days

