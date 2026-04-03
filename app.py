from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from werkzeug.middleware.proxy_fix import ProxyFix
import os
import requests

# إعدادات لضمان عمل الروابط بشكل آمن على الاستضافة
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
app.secret_key = 'primhall_ultra_key_2024'

# مسار قاعدة البيانات المخصص لمنصة Render لضمان صلاحيات الحفظ
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/primhall.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.String(50), primary_key=True)
    username = db.Column(db.String(100))
    points = db.Column(db.Integer, default=50)

with app.app_context():
    db.create_all()

# --- إعدادات ديسكورد المححدثة ---
CLIENT_ID = '1489184502424014868'
CLIENT_SECRET = 'fczQueuo4BS1qX9RG9beYDAVSwQyNLVH' # المفتاح الجديد الذي أرسلته
REDIRECT_URI = 'https://primehall-production.up.railway.app/callback'

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
        return "لم يتم استلام كود التحقق", 400

    data = {
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': REDIRECT_URI
    }
    
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    
    try:
        # طلب التوكن مع فحص حالة الاستجابة لمنع الانهيار
        response = requests.post('https://discord.com/api/oauth2/token', data=data, headers=headers, timeout=10)
        
        # إذا واجهت حظر Rate Limit (1015)، سيظهر السبب هنا بدلاً من صفحة الخطأ البيضاء
        if response.status_code != 200:
            return f"خطأ في الاتصال بديسكورد (Status {response.status_code}): {response.text}", response.status_code

        # الآن نقوم بتحويل البيانات إلى JSON بأمان بعد التأكد من نجاح الطلب
        token_data = response.json()
        access_token = token_data.get('access_token')
        
        user_response = requests.get('https://discord.com/api/users/@me', headers={'Authorization': f"Bearer {access_token}"})
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
        return f"خطأ داخلي في السيرفر: {str(e)}", 500

@app.route('/dashboard')
def dashboard():
    if not session.get('logged_in'): 
        return redirect(url_for('index'))
    user = User.query.get(session['user_id'])
    return render_template('dashboard.html', user=user, avatar=session['avatar'])

if __name__ == '__main__':
    app.run(debug=True)
