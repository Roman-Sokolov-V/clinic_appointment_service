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
- [ ]  POST: doctors/<id>/slots/ - bulk create slots
- [x] GET: doctors/<id>/slots/?from=&to=&available_only=true|false
- [x] list doctor’s slots; available_only=true returns slots with no current BOOKED appointment
- [ ]  GET: slots/<id>/ - get slot detail
- [ ]  DELETE: slots/<id>/ - delete slot (only if no appointment exists)
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
- [ ]  POST: appointments/ - create appointment (fails if slot already has a BOOKED appointment)
- [ ]  GET: appointments/?patient_id=...&doctor_id=...&status=...&from=&to= - list appointments
- [ ]  GET: appointments/<id>/ - get appointment detail
- [ ]  POST: appointments/<id>/cancel/ - cancel appointment; late-cancel may create CANCELLATION_FEE
- [ ]  POST: appointments/<id>/complete/ - mark completed
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
