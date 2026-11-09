# Razorpay test-mode integration

The backend now has server-side Razorpay order creation, checkout signature verification,
captured-payment status checking, and signed `payment.captured` webhook handling.

## Configure safely
- Use Razorpay **Test Mode** credentials only during development.
- Put `RAZORPAY_KEY_ID`, `RAZORPAY_KEY_SECRET`, and `RAZORPAY_WEBHOOK_SECRET` in the server environment.
- Never put the key secret or webhook secret in browser JavaScript, a public repository, or chat.
- Configure a webhook to `https://YOUR-DOMAIN/payments/webhook` for `payment.captured`.
- Keep the amount fixed on the server at ₹100 (10000 paise); do not accept an amount from the browser.

## Test flow
1. Register/login as a user.
2. Create a booking with `POST /bookings` using an approved expert's user ID.
3. Create an order with `POST /bookings/{booking_id}/payment/order`.
4. Use the returned `key_id`, `order_id`, and `amount` in Razorpay Checkout on the frontend.
5. Send the Checkout success values to `POST /payments/verify` with the user's bearer token.
6. The server checks the signature and fetches the payment; it unlocks the booking only if the payment is captured for exactly INR 100.
7. The signed webhook is an additional server-to-server confirmation path.

Razorpay docs: https://razorpay.com/docs/server-integration/python/test-app/

## Important limitations before launch
This is still a development starter, not a hosted/live platform. Add migrations for existing databases,
rate limiting, audit logs, privacy/consent flows, refunds/disputes handling, monitoring, HTTPS, backups,
and a security review. Real merchant onboarding and live payments must be managed by an authorized adult.
Chat/voice/video services are not included in this payment patch.
