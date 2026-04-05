# 🍔 Bitenation

A Django-powered web application with integrated M-Pesa (Safaricom) payment processing.

---

##  Features

- Django 5.0+ web framework
- M-Pesa STK Push payment integration via the Safaricom Daraja API
- Email notification support
- SQLite database (easily swappable for PostgreSQL/MySQL)
- Environment-based configuration for secure secrets management

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python / Django 5.0+ |
| Frontend | HTML / CSS |
| Database | SQLite |
| Payments | Safaricom M-Pesa Daraja API |
| Config | python-dotenv |

---

##  Prerequisites

- Python 3.10+
- pip
- A Safaricom Daraja API account ([register here](https://developer.safaricom.co.ke/))
- ngrok (or any tunneling tool) for local M-Pesa callback testing

---

##  Installation

1. **Clone the repository**

   ```bash
   git clone https://github.com/coi-exe/bitenation.git
   cd bitenation
   ```

2. **Create and activate a virtual environment**

   ```bash
   python -m venv venv
   source venv/bin/activate       # macOS/Linux
   venv\Scripts\activate          # Windows
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**

   Copy the example file and fill in your credentials:

   ```bash
   cp .env.example .env
   ```

   Then edit `.env`:

   ```env
   SECRET_KEY=your-django-secret-key

   # M-Pesa / Daraja API
   MPESA_CONSUMER_KEY=your-consumer-key
   MPESA_CONSUMER_SECRET=your-consumer-secret
   MPESA_SHORTCODE=your-shortcode
   MPESA_PASSKEY=your-passkey
   MPESA_CALLBACK_URL=https://your-ngrok-url.ngrok-free.app
   MPESA_BASE_URL=https://sandbox.safaricom.co.ke   # use https://api.safaricom.co.ke for production

   # Email
   EMAIL_HOST_USER=your-email@gmail.com
   EMAIL_HOST_PASSWORD=your-app-password
   DEFAULT_FROM_EMAIL=your-email@gmail.com
   ```

   > ⚠️ Never commit your real `.env` file to version control.

5. **Run database migrations**

   ```bash
   python manage.py migrate
   ```

6. **Start the development server**

   ```bash
   python manage.py runserver
   ```

   The app will be available at `http://127.0.0.1:8000`.

---

##  M-Pesa Integration

Bitenation uses the **Safaricom Daraja API** for mobile payments (STK Push).

For local development, M-Pesa requires a publicly accessible callback URL. Use [ngrok](https://ngrok.com/) to expose your local server:

```bash
ngrok http 8000
```

Copy the generated HTTPS URL into your `.env` as `MPESA_CALLBACK_URL`.

To switch from sandbox to production, update `MPESA_BASE_URL` to `https://api.safaricom.co.ke` and use your live credentials.

---

##  Project Structure

```
bitenation/
├── bitenation/         # Django project settings & root URLs
├── core/               # Main application (models, views, templates)
├── manage.py
├── requirements.txt
├── .env.example
└── bitenation.db       # SQLite database
```

---

##  Security Notes

- Rotate the `SECRET_KEY` before deploying to production.
- The `.env.example` file contains placeholder/sandbox credentials only — do not use them in production.
- Set `DEBUG=False` and configure `ALLOWED_HOSTS` in production.

---

##  License

This project is open source. Feel free to fork and build on it.
