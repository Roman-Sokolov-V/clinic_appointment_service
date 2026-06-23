
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
