from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from werkzeug.middleware.proxy_fix import ProxyFix
import os
import requests

# 1. إعدادات بيئة العمل (إجبارية للسيرفرات)
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

app = Flask(__name__)

# 2. حل مشكلة الـ HTTPS في Render لضمان وصول الجلسات (Sessions)
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# مفتاح سري قوي لتشفير بيانات المستخدم
app.secret_key = 'primhall_ultra_secure_2026_fixed'

# --- ⚙️ إعدادات ديسكورد (مدمجة وجاهزة) ---
CLIENT_ID = '1489184502424014868'
CLIENT_SECRET = '9TdmKUL_i34vX0N-6xnGq-udGD3DE354'
REDIRECT_URI = 'https://primehall.onrender.com/callback'
WEBHOOK_URL = "https://discord.com/api/webhooks/1489179488423252080/oXyTg6UgqM9Y9G84zvsOFz2vcu6mTwmAGC5ojeUFHbWItn2CttCZbBhsaR1_Qk2b5IYY"

# روابط Discord API الرسمية
AUTH_URL = f'https://discord.com/api/oauth2/authorize?client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}&response_type=code&scope=identify'
TOKEN_URL = 'https://discord.com/api/oauth2/token'
USER_API_URL = 'https://discord.com/api/users/@me'

def send_to_discord(title, msg, color=0x7289da):
    try:
        data = {"embeds": [{"title": title, "description": msg, "color": color}]}
        requests.post(WEBHOOK_URL, json=data, timeout=5)
    except:
        pass

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login-discord')
def login_discord():
    # توجيه المستخدم لصفحة تسجيل الدخول الرسمية
    return redirect(AUTH_URL)

@app.route('/callback')
def callback():
    # 1. استلام الكود من ديسكورد
    code = request.args.get('code')
    if not code:
        return "فشل الدخول: لم يتم استلام كود التحقق.", 400

    # 2. تبادل الكود بالـ Access Token (الطريقة اليدوية المضمونة)
    data = {
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': REDIRECT_URI
    }
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}

    try:
        # طلب التوكن
        token_response = requests.post(TOKEN_URL, data=data, headers=headers)
        token_response.raise_for_status()
        access_token = token_response.json().get('access_token')

        # 3. جلب بيانات المستخدم باستخدام التوكن الجديد
        user_headers = {'Authorization': f'Bearer {access_token}'}
        user_data = requests.get(USER_API_URL, headers=user_headers).json()

        # 4. حفظ البيانات في الجلسة (Session)
        session.permanent = True
        session['logged_in'] = True
        session['user_id'] = user_data['id']
        session['username'] = user_data['username']
        
        if user_data.get('avatar'):
            session['avatar'] = f"https://cdn.discordapp.com/avatars/{user_data['id']}/{user_data['avatar']}.png"
        else:
            session['avatar'] = "https://discord.com/assets/f78426a064bc98b57354.png"

        send_to_discord("✅ دخول ناجح", f"المستخدم **{user_data['username']}** دخل للموقع بنجاح.")
        return redirect(url_for('dashboard'))

    except Exception as e:
        print(f"Error during callback: {e}")
        return f"حدث خطأ فني أثناء تأكيد الدخول: {e}", 500

@app.route('/dashboard')
def dashboard():
    if not session.get('logged_in'):
        return redirect(url_for('index'))
    return render_template('dashboard.html', 
                           username=session['username'], 
                           avatar=session['avatar'])

@app.route('/claim_gift', methods=['POST'])
def claim_gift():
    if not session.get('logged_in'):
        return jsonify({'success': False, 'message': 'سجل دخولك أولاً'})
    
    code = request.form.get('gift_code')
    if code:
        send_to_discord("🎁 طلب هدية", f"المستخدم **{session['username']}** طلب هدية بالكود: `{code}`", 0xff6b6b)
        return jsonify({'success': True})
    return jsonify({'success': False})

if __name__ == '__main__':
    app.run(debug=True)
