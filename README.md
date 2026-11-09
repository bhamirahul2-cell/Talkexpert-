# TalkExpert backend starter

A small FastAPI + SQLite API starter for the TalkExpert prototype.

## Run locally
1. Install Python 3.11+.
2. Create and activate a virtual environment.
3. `pip install -r requirements.txt`
4. Set `TALKEXPERT_SECRET` to a long random value (do not use the example value).
5. `uvicorn app.main:app --reload`
6. Open `http://127.0.0.1:8000/docs` for interactive API docs.

## Included
- User/expert registration and login
- Password hashing and bearer-token authentication
- Expert profile submission and admin approval endpoints
- Approved expert directory
- ₹100 booking record in pending state
- Basic admin account-disable endpoint

## Important setup
This is a development starter, not a production-ready service. It does not process real payments,
send OTP/email verification, provide chat, or implement voice/video calls. Payment access must
only be enabled after verifying the payment provider's signed server webhook. Use HTTPS, a managed
database, rate limits, audit logs, backups, privacy/consent flows, and security review before launch.

For safety, create the first admin account through a controlled one-time setup script or secure
deployment process; do not expose public admin signup. Expert credentials must be checked by a
qualified human reviewer. Real merchant/payment accounts and legal business setup should be handled
by an authorized adult.
