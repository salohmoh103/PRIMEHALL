from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from requests_oauthlib import OAuth2Session
import os
import requests

app = Flask(__name__)
app.secret_key = 'primhall_ultra_key_2026'

# --- ⚙️ إعدادات ديسكورد الخاصة بك ---
CLIENT_ID = '1489184502424014868'
CLIENT_SECRET = '9TdmKUL_i34vX0N-6xnGq-udGD3DE354'
REDIRECT_URI = 'https://primehall.onrender.com/callback'
WEBHOOK_URL = "https://discord.com/api/webhooks/1489179488423252080/oXyTg6UgqM9Y9G84zvsOFz2vcu6mTwmAGC5ojeUFHbWItn2CttCZbBhsaR1_Qk2b5IYY"

# روابط Discord API
AUTH_BASE_URL = 'https://discord.com/api/oauth2/authorize'
TOKEN_URL = 'https://discord.com/api/oauth2/token'
SCOPE = ['identify', 'guilds'] # guilds لجلب معلومات السيرفرات لاحقاً

def send_to_discord(title, msg, color=0x7289da):
    data = {
        "embeds": [{"title": title, "description": msg, "color": color}]
    }
    requests.post(WEBHOOK_URL, json=data)

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
    discord = OAuth2Session(CLIENT_ID, state=session.get('oauth_state'), redirect_uri=REDIRECT_URI)
    token = discord.fetch_token(TOKEN_URL, client_secret=CLIENT_SECRET, authorization_response=request.url)
    user_data = discord.get('https://discord.com/api/users/@me').json()
    
    # حفظ بيانات المستخدم الرسمية
    session['logged_in'] = True
    session['user_id'] = user_data['id']
    session['username'] = user_data['username']
    session['avatar'] = f"https://cdn.discordapp.com/avatars/{user_data['id']}/{user_data['avatar']}.png"
    
    send_to_discord("✅ دخول جديد بالموقع", f"المستخدم **{user_data['username']}** سجل دخوله عبر ديسكورد الرسمي.")
    return redirect(url_for('dashboard'))

@app.route('/dashboard')
def dashboard():
    if not session.get('logged_in'):
        return redirect(url_for('index'))
    return render_template('dashboard.html', 
                           username=session['username'], 
                           avatar=session['avatar'])

@app.route('/claim_gift', methods=['POST'])
def claim_gift():
    code = request.form.get('gift_code')
    if code:
        send_to_discord("🎁 طلب هدية", f"المستخدم **{session['username']}** طلب هدية بالكود: `{code}`", 0xff6b6b)
        return jsonify({'success': True})
    return jsonify({'success': False})

if __name__ == '__main__':
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
    app.run(debug=True, port=5000)
