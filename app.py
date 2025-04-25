from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask import Flask, render_template_string, request, redirect, url_for, flash, jsonify
import requests
import os
import stripe

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Stripe-Konfiguration
STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY', '')
STRIPE_PUBLIC_KEY = os.environ.get('STRIPE_PUBLIC_KEY', '')
stripe.api_key = STRIPE_SECRET_KEY

def get_credits_packages():
    # Alle aktiven Prices mit Lookup-Key aus Stripe holen (sortiert nach Betrag)
    prices = stripe.Price.list(active=True, expand=['data.product'], limit=20)
    packages = []
    for price in prices['data']:
        lookup_key = price.get('lookup_key')
        if lookup_key and lookup_key.startswith('credits_'):
            # Credits-Zahl aus dem Lookup-Key extrahieren
            try:
                credits = int(lookup_key.split('_')[1])
            except Exception:
                credits = 0
            packages.append({
                'credits': credits,
                'lookup_key': lookup_key,
                'price_id': price['id'],
                'amount': price['unit_amount'] / 100,
                'currency': price['currency'].upper(),
            })
    # Nach Credits aufsteigend sortieren
    packages.sort(key=lambda x: x['credits'])
    return packages

# Gemini API-Konfiguration
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '')
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-pro-preview-03-25:generateContent"

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    credits = db.Column(db.Integer, default=5)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def generate_content_gemini(topic):
    if not GEMINI_API_KEY:
        return f"{topic} ist ein spannendes Thema. In diesem Artikel erfährst du alles Wichtige darüber und wie du es für dich nutzen kannst."
    headers = {"Content-Type": "application/json"}
    params = {"key": GEMINI_API_KEY}
    prompt = f"Schreibe einen hochwertigen, informativen und motivierenden Blogartikel über das Thema '{topic}'. Sprich den Leser direkt an, gib Tipps und Beispiele."
    data = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.7, "maxOutputTokens": 800}
    }
    try:
        response = requests.post(GEMINI_API_URL, headers=headers, params=params, json=data, timeout=30)
        response.raise_for_status()
        result = response.json()
        return result['candidates'][0]['content']['parts'][0]['text']
    except Exception as e:
        return f"Fehler bei der KI-Generierung: {e} (Fallback: {topic} ist ein spannendes Thema...)"

@app.route('/', methods=['GET', 'POST'])
@login_required
def index():
    content = ''
    title = 'AI Content Generator'
    if request.method == 'POST':
        topic = request.form.get('topic', 'Dein Thema')
        if current_user.credits <= 0:
            flash('Du hast keine Credits mehr. Bitte lade dein Konto auf.')
        else:
            content = generate_content_gemini(topic)
            current_user.credits -= 1
            db.session.commit()
            title = f'AI-generierter Content zu: {topic}'
    credits_packages = get_credits_packages()
    return render_template_string('''
        <!DOCTYPE html>
        <html lang="de">
        <head>
            <meta charset="utf-8">
            <title>AI Content Generator</title>
            <script src="https://js.stripe.com/v3/"></script>
            <style>
                body { font-family: Arial, sans-serif; background: #f8f8ff; padding: 40px; }
                .container { max-width: 600px; margin: auto; background: #fff; border-radius: 8px; box-shadow: 0 2px 8px #ddd; padding: 30px; }
                h1 { color: #2ecc40; }
                input[type=text], input[type=password] { width: 80%; padding: 8px; }
                button { background: #2ecc40; color: #fff; border: none; padding: 10px 18px; border-radius: 4px; font-weight: bold; }
                button:hover { background: #27ae35; }
                .result { margin-top: 30px; }
                .credits { float: right; color: #888; }
                .flash { color: red; }
                .pay { margin-top: 20px; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="credits">Credits: {{ current_user.credits }}</div>
                <h1>AI Content Generator</h1>
                <form method="POST">
                    <label for="topic">Thema/Nische:</label><br>
                    <input type="text" name="topic" id="topic" required placeholder="z.B. Affiliate Marketing, Fitness, ..."><br><br>
                    <button type="submit">Content generieren (1 Credit)</button>
                </form>
                {% with messages = get_flashed_messages() %}
                  {% if messages %}
                    <div class="flash">{{ messages[0] }}</div>
                  {% endif %}
                {% endwith %}
                {% if content %}
                <div class="result">
                    <hr>
                    <h2>{{ title }}</h2>
                    <p>{{ content|safe }}</p>
                </div>
                {% endif %}
                <div class="pay">
                  <form action="/create_checkout_session" method="POST">
                    {% for pkg in credits_packages %}
                      <button type="submit" name="lookup_key" value="{{ pkg['lookup_key'] }}">{{ pkg['credits'] }} Credits für {{ pkg['amount']|round(2) }} {{ pkg['currency'] }} kaufen</button>
                    {% endfor %}
                  </form>
                </div>
                <br>
                <a href="{{ url_for('logout') }}">Logout</a>
            </div>
        </body>
        </html>
    ''', content=content, title=title, credits_packages=credits_packages)

@app.route('/create_checkout_session', methods=['POST'])
@login_required
def create_checkout_session():
    lookup_key = request.form['lookup_key']
    # Preis-Objekt anhand Lookup-Key holen
    prices = stripe.Price.list(lookup_keys=[lookup_key], expand=['data.product'])
    if not prices['data']:
        flash('Preis nicht gefunden!')
        return redirect(url_for('index'))
    price = prices['data'][0]
    # Credits aus Lookup-Key bestimmen
    try:
        credits = int(lookup_key.split('_')[1])
    except Exception:
        credits = 0
    session = stripe.checkout.Session.create(
        payment_method_types=['card'],
        line_items=[{
            'price': price['id'],
            'quantity': 1,
        }],
        mode='payment',
        success_url=url_for('payment_success', credits=credits, _external=True),
        cancel_url=url_for('index', _external=True),
        client_reference_id=current_user.id
    )
    return redirect(session.url, code=303)

@app.route('/payment_success')
@login_required
def payment_success():
    credits = int(request.args.get('credits', 0))
    current_user.credits += credits
    db.session.commit()
    flash(f'Zahlung erfolgreich! {credits} Credits wurden deinem Konto gutgeschrieben.')
    return redirect(url_for('index'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if User.query.filter_by(username=username).first():
            flash('Benutzername existiert bereits!')
        else:
            user = User(username=username, password=password, credits=5)
            db.session.add(user)
            db.session.commit()
            flash('Registrierung erfolgreich! Bitte einloggen.')
            return redirect(url_for('login'))
    return render_template_string('''
        <!DOCTYPE html>
        <html lang="de">
        <head><meta charset="utf-8"><title>Registrieren</title></head>
        <body>
            <h2>Registrieren</h2>
            <form method="POST">
                <input name="username" placeholder="Benutzername" required><br>
                <input name="password" type="password" placeholder="Passwort" required><br>
                <button type="submit">Registrieren</button>
            </form>
            <a href="{{ url_for('login') }}">Zum Login</a>
            {% with messages = get_flashed_messages() %}
              {% if messages %}
                <div class="flash">{{ messages[0] }}</div>
              {% endif %}
            {% endwith %}
        </body></html>
    ''')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username, password=password).first()
        if user:
            login_user(user)
            return redirect(url_for('index'))
        else:
            flash('Login fehlgeschlagen!')
    return render_template_string('''
        <!DOCTYPE html>
        <html lang="de">
        <head><meta charset="utf-8"><title>Login</title></head>
        <body>
            <h2>Login</h2>
            <form method="POST">
                <input name="username" placeholder="Benutzername" required><br>
                <input name="password" type="password" placeholder="Passwort" required><br>
                <button type="submit">Login</button>
            </form>
            <a href="{{ url_for('register') }}">Registrieren</a>
            {% with messages = get_flashed_messages() %}
              {% if messages %}
                <div class="flash">{{ messages[0] }}</div>
              {% endif %}
            {% endwith %}
        </body></html>
    ''')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)
