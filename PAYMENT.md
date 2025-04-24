# Stripe/PayPal Integration (Credits-Aufladung)

- Zunächst Stripe als Payment-Provider für Credits-Aufladung (PayPal kann später ergänzt werden)
- Credits werden nach erfolgreicher Zahlung automatisch dem Nutzerkonto gutgeschrieben

## Flask-Stripe Integration (Minimalbeispiel)
- Stripe-Checkout für einfache Einmalzahlungen (z.B. 5€, 10€, 20€ für Credits)
- Nach Zahlung: Webhook empfängt Event, Credits werden erhöht

## Nächste Schritte
1. Stripe-Account anlegen (https://dashboard.stripe.com/register)
2. API-Keys in Render.com/Umgebung setzen: STRIPE_SECRET_KEY, STRIPE_PUBLIC_KEY
3. Webhook-URL in Stripe-Dashboard eintragen: /stripe_webhook

## Beispielpreise
- 5€ → 25 Credits
- 10€ → 60 Credits
- 20€ → 150 Credits

---

**Hinweis:**
- Die Integration ist DSGVO-konform, da Stripe die Zahlungsabwicklung übernimmt.
- Credits-Aufladung funktioniert sofort nach Deployment und Stripe-Konfiguration.
