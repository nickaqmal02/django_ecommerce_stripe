# Your Shop — Django E-Commerce with Stripe

A simple e-commerce app with Stripe payment gateway, cart, checkout, order tracking, and PDF receipts.

## Tech Stack

- Django 6.1
- Stripe (Checkout + Webhooks)
- WeasyPrint (PDF generation)
- Mailtrap (Email sandbox)
- django-unfold (Admin theme)
- Tailwind CSS + DaisyUI (Frontend)

## Setup (First Time)

```bash
# 1. Clone the repo
git clone git@github.com:nickaqmal02/django_ecommerce_stripe.git
cd django_ecommerce_stripe

# 2. Create virtual environment
python3.14 -m venv venv
source venv/bin/activate

# 3. Install dependencies
pip install django stripe weasyprint django-unfold

# 4. Run migrations
python manage.py migrate

# 5. Create superuser
python manage.py createsuperuser

# 6. Add test products (optional)
python manage.py shell
>>> from store.models import Category, Product
>>> Category.objects.create(name='Apparel')
>>> Product.objects.create(name='T-Shirt', description='Cotton tee', price=4900, category=Category.objects.first())
>>> exit()
```

## How to Run the Project

You need **TWO terminals running** — Django server + Stripe webhook listener.

### Terminal 1 — Django Server

```bash
cd ~/degree/ecommerce_project
source venv/bin/activate
python manage.py runserver 8090
stripe listen --forward-to localhost:8090/webhook/ --all-snapshot



```

Server runs at: http://localhost:8090/

### Terminal 2 — Stripe Webhook Listener

```bash
stripe listen --forward-to localhost:8090/webhook/ --all-snapshot
```

This forwards Stripe's webhook events to your Django server. Without this, payments will show as PENDING forever.

### Stripe CLI Setup (First Time Only)

```bash
# Install Stripe CLI
brew install stripe/stripe-cli/stripe

# Login with your Stripe account
stripe login

# Verify connection
stripe --version
```

### Stripe Dashboard

- Test mode: https://dashboard.stripe.com/test
- API keys: https://dashboard.stripe.com/test/apikeys
- Test card: `4242 4242 4242 4242`
- Expiry: any future date (e.g. `12/30`)
- CVC: any 3 digits (e.g. `123`)

## Mailtrap Email Setup

1. Go to https://mailtrap.io → sign up (free)
2. Create a sandbox inbox
3. Copy SMTP credentials
4. Update `shopconfig/settings.py`:

```python
MAILERS = {
    'default': {
        'BACKEND': 'django.core.mail.backends.smtp.EmailBackend',
        'OPTIONS': {
            'host': 'sandbox.smtp.mailtrap.io',
            'port': 587,
            'use_tls': True,
            'username': 'YOUR_USERNAME',
            'password': 'YOUR_PASSWORD',
        },
    },
}
```

## Environment Variables

Update these in `shopconfig/settings.py`:

```python
STRIPE_SECRET_KEY = 'sk_test_...'       # from Stripe dashboard
STRIPE_PUBLISHABLE_KEY = 'pk_test_...'  # from Stripe dashboard
```

Webhook signing secret is in `store/views.py`:
```python
endpoint_secret = 'whsec_...'  # from `stripe listen` output
```

## Features

- Product catalog with categories
- Multiple images per product
- Session-based shopping cart
- Checkout with email, name, phone, address
- Stripe payment (card + FPX)
- Webhook confirmation (PENDING → PAID)
- Email receipt sent to customer
- Order tracking page (enter order ID)
- PDF receipt download
- Admin: courier + tracking number management
- Unfold dark theme admin

## Admin Access

```
URL: http://localhost:8090/admin/
Username: admin
Password: admin123
```

## Payment Flow

```
Customer browses → adds to cart → checkout form
→ Stripe checkout page → pays with card
→ Stripe sends webhook to /webhook/
→ Django updates Order.paid = True
→ Email receipt sent via Mailtrap
→ Customer redirected to success page
→ Can track order with order ID (e.g. ORD-001)
```

## SSH Key Setup

```bash
# Generate key
ssh-keygen -t ed25519 -C "your@email.com"
# Press Enter for default location (~/.ssh/id_ed25519)

# Start SSH agent
eval "$(ssh-agent -s)"

# Add key
ssh-add ~/.ssh/id_ed25519

# Copy public key
pbcopy < ~/.ssh/id_ed25519.pub

# Add to GitHub → Settings → SSH and GPG keys → New SSH key

# Test
ssh -T git@github.com
```

## Remove Secret from Git History

If you accidentally commit a secret (SSH key, API key):

```bash
# 1. Remove file from ALL commits
git filter-branch --force \
  --index-filter 'git rm --cached --ignore-unmatch <filename>' \
  --prune-empty --tag-name-filter '*' -- --all

# 2. Clean up old refs
rm -rf .git/refs/original/
git reflog expire --expire=now --all
git gc --prune=now --aggressive

# 3. Verify (empty = gone)
git log --all --diff-filter=A -- <filename>

# 4. Force push
git push origin master --force
```
