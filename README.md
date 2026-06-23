# 🏥 Clinic Appointment & Payment System

A robust, enterprise-grade asynchronous backend ecosystem designed to digitize a private clinic's operational pipeline. The system automates doctor schedule management, streamlines patient bookings, handles complex multi-method payment splits, and features a completely standalone, client-facing Telegram Bot that acts as a native mobile front-end.
## 🛠️ Tech Stack & Infrastructure

### Backend Engine
* **Core Framework:** Python 3.14, Django 5.x, Django REST Framework (DRF)
* **Authentication:** Simple JWT (OAuth 2.0 with rotation & blacklists), Google OAuth2
* **Database & Async Workers:** PostgreSQL, Celery (Distributed Task Queue), Celery-Beat (Database Scheduler)


### Client Ecosystem (Telegram Bot)

- Aiogram 3.x (Asynchronous Telegram Bot framework)
- Caching & State Management: Redis (High-performance caching layer)
- PostgreSQL

### DevOps & Integration
* **Containerization:** Docker, Docker Compose (isolated service definitions)
* **Message Broker:** RabbitMQ
* **Monitoring:** Flower (Real-time Celery web-dashboard)
* **Payment Gateways:** Stripe API, integrated via Stripe CLI webhook proxies

## 🚀 Quick Start (Local Development)
1. Clone & Configure Environment

Clone the repository and spin up your environment configurations:
```Bash
git https://github.com/Roman-Sokolov-V/clinic_appointment_service
cd clinic_appointment_service
```
Create a .env file in the root directory and in telegram_bot/  directory based on .env.example
and supply your database keys, Stripe secrets, and Telegram Bot tokens.
2. Launch the Application Stack

The entire environment—including database, caching, background workers, and frontend bot:
```Bash
docker compose -f dev-docker-compose.yml -d --build
```
3. Stream Stripe Webhooks Local

To capture and forward checkout session webhooks from Stripe's cloud down to your local running Django container:
```Bash
stripe listen --forward-to localhost:8000/clinic/stripe/webhook/
```
📚 Project Documentation & Deep Dives

To prevent a cluttered main layout, detailed guides are separated into specialized files within the
documentation folder (docs/):

## 📚 Project Documentation & Deep Dives

To prevent a cluttered main layout, detailed guides are separated into specialized files within the documentation folder (`docs/`). Click on any guide below to open its detailed breakdown:

* 🎯 **[Task & Architectural Solutions](docs/task_and_architectural_solutions.md)** – A deep dive into initial specifications, domain entity modifications, and database-level snapshotting justifications.
* 💻 **[Frontend & API Integration Guide](docs/frontend_guide.md)** – Complete endpoints overview, JSON layouts, limit/offset pagination structures, and strict rules for JWT token refresh cycles.
* 🔄 **[Business Logic & Workflows](docs/business_logic.md)** – Detailed step-by-step documentation of core clinic workflows, including state transitions (Booked ➡️ No-Show/Completed) and automated task processing rules.
* 💳 **[Stripe Payment Integration](docs/stripe_integration.md)** – A comprehensive DevOps deployment guide for configuring local environment keys, installing the Stripe CLI proxy tool, authenticating sandbox tunnels, and forwarding real-time webhook events to your running Django container.

## 💡 Key Architectural Highlights

This project was built to solve real-world problems with production-grade engineering patterns. Here is how the system stands out:  
### ⚡ Standalone Bot Microservice

Instead of treating the Telegram Bot as a minor background notification worker, 
it was engineered as a completely standalone frontend microservice. 
It communicates with the backend strictly through HTTP REST API endpoints. 
This means the entire bot can be decoupled into its own repository and deployed on an entirely 
separate physical server without breaking a single feature.
### ⏳ Distributed Event-Driven Architecture (Celery & RabbitMQ)
* **Non-Blocking Background Workers:** To protect the API response times from being bottlenecked by third-party network over-overhead, any heavy operations—such as dispatching Telegram notifications to staff, syncing with Stripe, or processing logic hooks—are offloaded asynchronously to **Celery workers** using **RabbitMQ** as a reliable message broker.
* **Dynamic Database-Driven Scheduling (Celery-Beat):** Periodic automation is managed via `django-celery-beat` with its `DatabaseScheduler`. Instead of hardcoding task crontabs, scheduling rules are stored directly in the database. This enables automated background checks (such as automatically scanning expired time slots and updating unattended visits to `NO_SHOW` status right after a slot ends) to run dynamically without requiring service restarts or configuration deployments.
### 🔐 Multi-Tier Security & Token Handling

#### API Layer Security:  
Leverages DRF Simple JWT with strict token rotation and active blacklisting. If an access token expires, refreshing it issues a brand new refresh token and destroys the previous one, mitigating replay attacks.
#### Smart Distributed Session Storage:  
The bot optimizes performance and security by splitting token storage: short-lived API access_tokens are kept in Redis for lightning-fast request authentication middleware, while long-lived session refresh_tokens remain secured in PostgreSQL on the backend.

#### Frictionless Social Sign-In:  
Integrated Google OAuth2 alongside standard credentials to allow effortless patient registration and higher user onboarding conversion rates.

### 💳 Flexible Payment Abstraction (Vendor Agnostic)

While the core requirement requested Stripe, the system was refactored to decouple the database from specific vendors by replacing explicit Stripe-specific columns with a generic method field and a provider_metadata JSON scheme. Backed by a clean Abstract Payment Service pattern, the architecture allows the clinic to easily scale and switch to alternative gateways (like PayPal or regional processors) simply by implementing a new class inheriting from the abstract layer.
### 🛡️ Data Resiliency & Business Edge-Cases

#### Stateless Callback Pipelines: 
The booking wizard inside the Telegram Bot avoids stateful caching engines (like Redis FSM states). By packaging doctor and slot metadata directly inside encrypted, signed inline button CallbackData payloads, the user flow is immune to state timeouts or bot service restarts.

#### Financial Snapshots: 
When an appointment is created, the system locks in the current pricing, cancellation window parameters, and late fees from a singleton GlobalClinicSettings model. If management changes prices tomorrow, historical data and pending bills remain accurate and untampered with.