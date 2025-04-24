# Deployment-Guide: AI Content Generator

## 1. Vorbereitung
- Stelle sicher, dass alle Abhängigkeiten in `requirements.txt` stehen.
- Die Datei `Procfile` ist für das Deployment auf Render.com oder Heroku notwendig.

## 2. Deployment auf Render.com (empfohlen)
1. Gehe auf https://render.com und logge dich ein (GitHub-Account möglich).
2. Klicke auf "New Web Service".
3. Verbinde dein GitHub-Repo oder lade den Code als ZIP hoch.
4. Wähle als Startbefehl: `web: python app.py` (steht bereits im Procfile).
5. Setze im Dashboard die Umgebungsvariablen:
   - `GEMINI_API_KEY=DEIN_KEY`
   - `SECRET_KEY=dein_geheimer_string`
6. Deployen und den öffentlichen Link teilen!

## 3. Payment-Integration (Stripe/PayPal)
- Stripe/PayPal lässt sich nachträglich als Checkout-Button oder Credits-Aufladefunktion integrieren.
- Empfohlen: Erst Deployment, dann Payment live schalten.

## 4. App an den Mann bringen
- Teile den öffentlichen Link auf Social Media, im Profil-README, auf X, LinkedIn, Foren etc.
- Zeige in Demos, wie einfach Nutzer Content generieren und Credits kaufen können.

---

**Fragen?** Ich kann den Payment-Flow oder eine Schritt-für-Schritt-Anleitung für Stripe/PayPal direkt ergänzen!
