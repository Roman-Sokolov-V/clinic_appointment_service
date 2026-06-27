1. Project Overview & Context

A small private clinic books appointments by phone and writes everything into paper notebooks. Patients forget appointments, doctors’ schedules overlap, and receptionists can’t track payments or apply late-cancellation fees.
Core Requirements

Functional: Web-based, manage doctors & availability, manage patients, handle appointments (book, cancel, complete), display notifications, handle payments.

Non-functional: 5 concurrent users, up to 1000 active books, 50k appointments/year, ~30MB storage allocation per year.

Interface: Fully functional browsable API interface (DRF) acting as the backend, with an asynchronous Telegram Bot client for end-users.

2. Resource Models & Architectural Evolutions  

👤👤 User (Patient) & Authentication

Original Spec: Email: str, First name: str, Last name: str, Password: str, Is staff: bool

Implementation Status: Integrated via a Custom User Model.

Authentication Evolution (OAuth2 Integration): In addition to standard JWT token pairs, the system was upgraded to support OAuth2 authentication via Google.

Why? To lower the friction of user onboarding. Instead of forcing patients to go through a traditional 
email-verification and password-creation loop, they can securely authenticate using their existing Google accounts. 
The system automatically provisions a safe JWT session upon a successful OAuth2 callback, aligning the platform 
with modern web and mobile application standards.  

🗂️ Specialization

Original Spec: Name: str (unique), Code: slug (unique), Description: str | null

Implementation Status: Implemented. Serves as a stable identifier for doctor filtering.

🩺 Doctor & DoctorSlot

Original Spec: * Doctor: First name, Last name, Specializations (M2M), Price per visit (decimal)

DoctorSlot: Doctor id, Start (datetime), End (datetime)

rivacy Enhancement: The slots endpoint was modified so that regular non-admin users can only view unbooked slots (available_only=true). Full visibility is restricted to staff to prevent data leaks of other patients' schedules.

📅 Appointment Model
Python

### Original Spec Fields:
#### - Doctor slot id: int
#### - Patient id: int
#### - Status: Enum (BOOKED | COMPLETED | CANCELLED | NO_SHOW)
#### - Booked at: datetime
#### - Completed at: datetime | null
#### - Price: decimal

APPOINTMENT_STATUS = (
    ('BOOKED', 'booked'),
    ('COMPLETED', 'completed'),
    ('CANCELED', 'canceled'),
    ('NO_SHOW', 'no_show'),
)
```
class Appointment(models.Model):
    slot = models.ForeignKey(DoctorSlot, on_delete=models.CASCADE, related_name='appointments')
    patient = models.ForeignKey(AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='appointments')
    status = models.CharField(max_length=100, choices=APPOINTMENT_STATUS, default='BOOKED')
    booked_at = models.DateField(auto_now_add=True)
    completed_at = models.DateField(null=True, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)  
    percent_fee = models.IntegerField(default=10) 
    window_fee = models.IntegerField(default=120)  
```
💡 Architectural Evolution:

Dynamic Snapshotting: The price, percent_fee, and window_fee are snapshotted into the Appointment instance at the exact moment of creation (copied from Doctor.price_per_visit and GlobalClinicSettings).

Why? If the clinic management updates a doctor's pricing or changes global fine policies later, existing historical appointments and current pending invoices remain unchanged. This preserves financial integrity and matches real-world clinic workflows.

💳 Payment Model
Python

### Original Spec Fields (Vendor-Locked):
#### - Status: Enum (PENDING | PAID | EXPIRED)
#### - Type: Enum (CONSULTATION | CANCELLATION_FEE | NO_SHOW_FEE)
#### - Appointment id: int
#### - Session url: Url / Session id: str (Stripe-specific)
#### - Money to pay: decimal
```
PAYMENT_STATUS = (
    ('PENDING', 'pending'),
    ('PAID', 'paid'),
    ('EXPIRED', 'expired'),
    ('REFUNDED', 'refunded'),
    ('REFUND_PENDING', 'refund_pending'),
)

PAYMENT_TYPE = (
    ('CONSULTATION', 'consultation'),
    ('NO_SHOW_FEE', 'no show fee'),
)

PAYMENT_METHOD = (
    ('CASH', 'Cash'),
    ('STRIPE', 'Stripe'),
)

class Payment(models.Model):
    status = models.CharField(max_length=100, choices=PAYMENT_STATUS, default='PENDING')
    type = models.CharField(max_length=100, choices=PAYMENT_TYPE, default='CONSULTATION')
    method = models.CharField(max_length=100, choices=PAYMENT_METHOD, default='STRIPE')
    appointment = models.ForeignKey(Appointment, on_delete=models.CASCADE, related_name='payments')
    money_to_pay = models.DecimalField(max_digits=10, decimal_places=2)
    provider_metadata = models.JSONField(default=dict, blank=True, null=True)
```
💡 Architectural Evolution:

Decoupling from Stripe: The original requirements coupled the database schema directly to Stripe fields (session_id, session_url). This model was refactored to introduce method (e.g., CASH, STRIPE) and replaced specific string fields with a flexible provider_metadata JSON field.

Why? This allows the clinic to support physical cash on-site at the reception desk or easily scale to alternative payment gateways (e.g., PayPal, LiqPay) without running schema migrations.

Abstract Service Pattern: On the backend engine level, an Abstract Payment Service class was implemented. The StripePaymentService inherits from this abstract base, ensuring that adding any future provider only requires writing a new class that reuses the predefined abstract methods, making the platform highly modular.

⚙️ New Component: Global Clinic Settings

To avoid hardcoded magic numbers for business rules, a dedicated settings configuration model was added:
Python
```
class GlobalClinicSettings(models.Model):
    fee = models.IntegerField(
        default=10, # in %
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    fee_window = models.IntegerField(
        default=120, # in minutes
        validators=[MinValueValidator(0)]
    )
    singleton_id = models.IntegerField(default=1, editable=False)
```
💡 Architectural Evolution:

Why? Implemented as a Singleton model to allow administrators to dynamically manage global properties—such as the late-cancellation penalty percentage (fee) and the deadline window (fee_window in minutes)—directly from the administrative control panel without code redeployments.

3. Client & Infrastructure Components
Python

### Original Spec Requirements:
#### - Notifications Service (Telegram): Simple notifications sent to clinic administrators
####   about appointments (booked, cancelled, completed, no-show) and successful payments.
#### - No front-end is required (browsable DRF interface only).

💡 Architectural Evolution & Client-Facing Bot:

Full-Scale Client Interface: Instead of building just a passive admin-notification script as requested, the system features a fully-fledged, asynchronous Telegram Bot for end-users built with aiogram 3.x. The bot acts as the complete front-end application for patients, allowing them to browse specializations, select doctors, view real-time available schedules, choose payment methods, and manage their bookings.

Why? A pure backend with a browsable API feels incomplete as a real-world product. Transitioning the bot into a primary client-facing interface solves the front-end gap, providing a polished and native UX directly inside a messenger.

🔐 Stateless Architecture & Token Distribution:

To maintain security across boundaries, the Telegram Bot implements a robust authentication storage strategy:

Access Tokens in Redis: Short-lived access_token strings are stored in a high-speed Redis cache layer. This ensures lightning-fast read operations during authenticated API requests and allows token middleware to inject authorization headers instantly.

Refresh Tokens in PostgreSQL: Long-lived refresh_token strings are safely persisted in PostgreSQL on the backend. This allows for strict session tracking, secure token rotation, and remote logout/blacklisting capabilities.

🐳 Microservice Isolation:

Why? The Telegram Bot is engineered as a completely standalone microservice. It is fully decoupled from the core Django engine and communicates with the backend exclusively via standard HTTP REST API endpoints.

This architectural boundary ensures that the bot service can be decoupled from the primary repository, scaled independently, or moved to a completely different physical server without any code regression or loss of functionality.