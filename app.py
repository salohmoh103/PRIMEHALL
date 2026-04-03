from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from werkzeug.middleware.proxy_fix import ProxyFix
import os
import requests

# إعدادات البيئة لضمان عمل الروابط بشكل آمن
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

app = Flask(__name__)

# تفعيل ProxyFix لضمان قراءة الروابط بشكل صحيح على Railway
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
app.secret_key = 'primhall_ultra_key_2024'

# تعديل مسار قاعدة البيانات ليعمل محلياً على Railway ويحفظ البيانات
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///primhall.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.String(50), primary_key=True)
    username = db.Column(db.String(100))
    points = db.Column(db.Integer, default=50)

with app.app_context():
    db.create_all()

# --- إعدادات ديسكورد المحدثة ---
CLIENT_ID = '1489184502424014868'
CLIENT_SECRET = 'hgi1l6_zIzgjZpUsKU0TiptKOENdz8m6' # السيكرت الجديد الذي أرسلته الآن
# الرابط المعتمد لمنصة Railway
REDIRECT_URI = 'https://primehall-production.up.railway.app/callback'
WEBHOOK_URL = "https://discord.com/api/webhooks/1489179488423252080/oXyTg6UgqM9Y9G84zvsOFz2vcu6mTwmAGC5ojeUFHbWItn2CttCZbBhsaR1_Qk2b5IYY"

def send_webhook(title, message, color=0x7289da):
    try:
        payload = {"embeds": [{"title": title, "description": message, "color": color}]}
        requests.post(WEBHOOK_URL, json=payload, timeout=10)
    except Exception as e:
        print(f"Webhook Error: {e}")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login-discord')
def login():
    scope = "identify"
    auth_url = f"https://discord.com/api/oauth2/authorize?client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}&response_type=code&scope={scope}"
    return redirect(auth_url)

@app.route('/callback')
def callback():
    code = request.args.get('code')
    if not code:
        return "خطأ: لم يتم استلام رمز التحقق من ديسكورد.", 400

    data = {
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': REDIRECT_URI
    }
    
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    
    try:
        # طلب التوكن مع فحص الحالة لمنع الانهيار
        token_response = requests.post('https://discord.com/api/oauth2/token', data=data, headers=headers, timeout=10)
        
        if token_response.status_code != 200:
            return f"Discord Auth Failed: {token_response.text}", token_response.status_code
        
        token_data = token_response.json()
        access_token = token_data.get('access_token')
        
        user_response = requests.get('https://discord.com/api/users/@me', headers={'Authorization': f"Bearer {access_token}"}, timeout=10)
        user_info = user_response.json()
        
        user = User.query.get(user_info['id'])
        if not user:
            user = User(id=user_info['id'], username=user_info['username'], points=50)
            db.session.add(user)
            db.session.commit()
        
        session['logged_in'] = True
        session['user_id'] = user.id
        session['avatar'] = f"https://cdn.discordapp.com/avatars/{user.id}/{user_info['avatar']}.png" if user_info.get('avatar') else "https://discord.com/assets/f78426a064bc98b57354.png"
        
        return redirect(url_for('dashboard'))
        
    except Exception as e:
        return f"حدث خطأ برمجى: {str(e)}", 500

@app.route('/dashboard')
def dashboard():
    if not session.get('logged_in'): 
        return redirect(url_for('index'))
    user = User.query.get(session['user_id'])
    return render_template('dashboard.html', user=user, avatar=session['avatar'])

@app.route('/exchange_role', methods=['POST'])
def exchange_role():
    if not session.get('logged_in'): 
        return jsonify({'success': False, 'message': 'يرجى تسجيل الدخول أولاً'})
    
    user = User.query.get(session['user_id'])
    role_name = request.form.get('name')
    cost = int(request.form.get('cost'))
    
    if user.points >= cost:
        user.points -= cost
        db.session.commit()
        send_webhook("🎖️ طلب استبدال رتبة", f"👤 المستخدم: **{user.username}**\n🆔 الأيدي: `{user.id}`\n👑 الرتبة المطلوبة: **{role_name}**\n💰 الخصم: {cost} نقطة", 0x2ecc71)
        return jsonify({'success': True, 'new_points': user.points})
    
    return jsonify({'success': False, 'message': 'نقاطك غير كافية لهذا الاستبدال!'})

@app.route('/claim_gift', methods=['POST'])
def claim_gift():
    if not session.get('logged_in'): 
        return jsonify({'success': False})
    
    code = request.form.get('gift_code')
    send_webhook("🎁 كود هدية جديد", f"👤 المستخدم: {session['user_id']}\n🎫 الكود: `{code}`", 0xff6b6b)
    return jsonify({'success': True})

if __name__ == '__main__':
    app.run(debug=True)
