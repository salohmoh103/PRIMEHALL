from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from requests_oauthlib import OAuth2Session
import os
import requests

# هـام جداً: هذا السطر يجب أن يكون في الأعلى ليعمل تسجيل الدخول على Render
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

app = Flask(__name__)

# تم وضع كلمة سر عشوائية قوية لتأمين الجلسات (Sessions)
app.secret_key = 'primhall_ultra_secure_key_992288'

# --- ⚙️ إعدادات ديسكورد الخاصة بك ---
CLIENT_ID = '1489184502424014868'
CLIENT_SECRET = '9TdmKUL_i34vX0N-6xnGq-udGD3DE354'
REDIRECT_URI = 'https://primehall.onrender.com/callback'
WEBHOOK_URL = "https://discord.com/api/webhooks/1489179488423252080/oXyTg6UgqM9Y9G84zvsOFz2vcu6mTwmAGC5ojeUFHbWItn2CttCZbBhsaR1_Qk2b5IYY"

# روابط Discord API
AUTH_BASE_URL = 'https://discord.com/api/oauth2/authorize'
TOKEN_URL = 'https://discord.com/api/oauth2/token'
SCOPE = ['identify'] # تم اختصاره لضمان السرعة وعدم حدوث أخطاء في الصلاحيات

def send_to_discord(title, msg, color=0x7289da):
    try:
        data = {
            "embeds": [{"title": title, "description": msg, "color": color}]
        }
        requests.post(WEBHOOK_URL, json=data)
    except:
        pass

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login-discord')
def login_discord():
    discord = OAuth2Session(CLIENT_ID, scope=SCOPE, redirect_uri=REDIRECT_URI)
    authorization_url, state = discord.authorization_url(AUTH_BASE_URL)
    session['oauth_state'] = state
    return redirect(authorization_url)

@app.route('/callback')
def callback():
    try:
        discord = OAuth2Session(CLIENT_ID, state=session.get('oauth_state'), redirect_uri=REDIRECT_URI)
        token = discord.fetch_token(TOKEN_URL, client_secret=CLIENT_SECRET, authorization_response=request.url)
        user_data = discord.get('https://discord.com/api/users/@me').json()
        
        # حفظ بيانات المستخدم الرسمية في الجلسة
        session['logged_in'] = True
        session['user_id'] = user_data['id']
        session['username'] = user_data['username']
        
        # التأكد من وجود صورة شخصية أو وضع صورة افتراضية
        if user_data.get('avatar'):
            session['avatar'] = f"https://cdn.discordapp.com/avatars/{user_data['id']}/{user_data['avatar']}.png"
        else:
            session['avatar'] = "https://discord.com/assets/f78426a064bc98b57354.png"
        
        send_to_discord("✅ دخول جديد بالموقع", f"المستخدم **{user_data['username']}** سجل دخوله عبر ديسكورد.")
        return redirect(url_for('dashboard'))
    except Exception as e:
        print(f"Error in callback: {e}")
        return f"حدث خطأ أثناء تسجيل الدخول: {e}", 500

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
        return jsonify({'success': False, 'message': 'يجب تسجيل الدخول أولاً'})
        
    code = request.form.get('gift_code')
    if code:
        send_to_discord("🎁 طلب هدية", f"المستخدم **{session['username']}** طلب هدية بالكود: `{code}`", 0xff6b6b)
        return jsonify({'success': True})
    return jsonify({'success': False})

if __name__ == '__main__':
    app.run(debug=True, port=5000)
