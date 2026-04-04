from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from werkzeug.middleware.proxy_fix import ProxyFix
import os
import requests

os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
app.secret_key = 'primhall_ultra_key_2024'

# قاعدة بيانات Railway
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///primhall.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.String(50), primary_key=True)
    username = db.Column(db.String(100))
    points = db.Column(db.Integer, default=50)
    role_name = db.Column(db.String(50), default="عضو") 

with app.app_context():
    db.create_all()

CLIENT_ID = '1489184502424014868'
CLIENT_SECRET = 'ullNU8GFb76QcOnVl1hs3FSZepsqFpn1'
REDIRECT_URI = 'https://primehall-production.up.railway.app/callback'
WEBHOOK_URL = "https://discord.com/api/webhooks/1489179488423252080/oXyTg6UgqM9Y9G84zvsOFz2vcu6mTwmAGC5ojeUFHbWItn2CttCZbBhsaR1_Qk2b5IYY"

def send_webhook(title, message, color=0x7289da):
    try:
        payload = {"embeds": [{"title": title, "description": message, "color": color}]}
        requests.post(WEBHOOK_URL, json=payload, timeout=10)
    except: pass

@app.route('/admin/set_role/<user_id>/<new_role>')
def set_role(user_id, new_role):
    user = User.query.get(user_id)
    if user:
        user.role_name = new_role
        db.session.commit()
        return f"✅ تم تحديث رتبة {user.username} إلى {new_role} بنجاح!"
    return "❌ المستخدم غير موجود", 404

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login-discord')
def login():
    auth_url = f"https://discord.com/api/oauth2/authorize?client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}&response_type=code&scope=identify"
    return redirect(auth_url)

@app.route('/callback')
def callback():
    code = request.args.get('code')
    data = {'client_id': CLIENT_ID, 'client_secret': CLIENT_SECRET, 'grant_type': 'authorization_code', 'code': code, 'redirect_uri': REDIRECT_URI}
    response = requests.post('https://discord.com/api/oauth2/token', data=data, headers={'Content-Type': 'application/x-www-form-urlencoded'})
    token_data = response.json()
    access_token = token_data.get('access_token')
    user_info = requests.get('https://discord.com/api/users/@me', headers={'Authorization': f"Bearer {access_token}"}).json()
    
    user = User.query.get(user_info['id'])
    if not user:
        user = User(id=user_info['id'], username=user_info['username'], points=50)
        db.session.add(user)
        db.session.commit()
    
    admin_url = f"https://primehall-production.up.railway.app/admin/set_role/{user.id}/الرتبة_هنا"
    send_webhook("👤 دخول مستخدم", f"الاسم: **{user.username}**\nلتعيين رتبة: [اضغط هنا]({admin_url})")

    session['logged_in'] = True
    session['user_id'] = user.id
    session['avatar'] = f"https://cdn.discordapp.com/avatars/{user.id}/{user_info['avatar']}.png" if user_info.get('avatar') else "https://discord.com/assets/f78426a064bc98b57354.png"
    return redirect(url_for('dashboard'))

@app.route('/dashboard')
def dashboard():
    if not session.get('logged_in'): return redirect(url_for('index'))
    user = User.query.get(session['user_id'])
    return render_template('dashboard.html', user=user, avatar=session['avatar'])

@app.route('/exchange_role', methods=['POST'])
def exchange_role():
    if not session.get('logged_in'): return jsonify({'success': False})
    user = User.query.get(session['user_id'])
    name = request.form.get('name'); cost = int(request.form.get('cost'))
    if user.points >= cost:
        user.points -= cost
        db.session.commit()
        send_webhook("🛒 طلب رتبة", f"المستخدم {user.username} طلب: {name}")
        return jsonify({'success': True, 'new_points': user.points})
    return jsonify({'success': False, 'message': 'نقاط غير كافية'})

@app.route('/claim_gift', methods=['POST'])
def claim_gift():
    if not session.get('logged_in'): return jsonify({'success': False})
    code = request.form.get('gift_code')
    send_webhook("🎁 كود جديد", f"المستخدم {session['user_id']} أرسل كود: {code}")
    return jsonify({'success': True})

if __name__ == '__main__':
    app.run(debug=True)
