import os  # osモジュールをインポートします（シークレットキーの生成に使用）
from flask import Flask, render_template, request, redirect, url_for, session, flash  # Flask本体と、Web処理に必要な関数群をインポートします
import datetime  # タイムスタンプのために datetime をインポートします

# Flaskアプリケーションを初期化（インスタンスを作成）します
app = Flask(__name__)  # __name__ は現在のファイル名(app)を意味します

# セッション管理のためのシークレットキーを設定します（ログイン状態の維持に必須）
app.secret_key = os.urandom(24)  # os.urandom(24)で24バイトのランダムなキーを生成します

# --- ユーザーデータベース (ID, パスワード, メールアドレスを格納) ---
DUMMY_USERS = {
    "user123": {"password": "password123", "email": "user@example.com"},  # ユーザーID "user123" の情報
    "admin": {"password": "adminpass", "email": "admin@example.com"}  # ユーザーID "admin" の情報
}  # 辞書の終わりです

# --- アプリ内データ（データベースの代わり） ---
SUPPORT_REQUESTS = []  # 支援要請を格納するリスト
SAFETY_CHECKS = {}  # 安否確認を格納する辞書（ユーザーIDをキーにして最新情報を上書き）
SOS_REPORTS = []  # SOSレポートを格納するリスト
# チャット機能用のデータ
DUMMY_GROUPS = {
    "family": "家族グループ",
    "shelter_a": "A避難所チーム"
}
CHAT_MESSAGES = {
    "family": [
        {"user_id": "admin", "text": "テストメッセージです", "timestamp": "2025/10/31 10:00"}
    ],
    "shelter_a": []
}

# ▼▼▼ コミュニティ機能用のデータを追加 ▼▼▼
COMMUNITY_POSTS = [
    {
        "user_id": "admin",
        "title": "（テスト投稿）水配布の情報",
        "content": "市役所前で15時から水が配布されるそうです。",
        "timestamp": "2025/10/31 09:00"
    }
]


# ▲▲▲ ここまで追加 ▲▲▲


# -------------------------------------------------------------------
# ルーティング関数
# -------------------------------------------------------------------

@app.route('/')
def index():
    """ルートURL: ログイン状態に応じてリダイレクト"""
    if 'user_id' in session:
        return redirect(url_for('home'))
    else:
        return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    """ログイン画面の表示 (GET) と ログイン処理 (POST)"""
    if 'user_id' in session:
        return redirect(url_for('home'))

    if request.method == 'POST':
        user_id = request.form['user_id']
        password = request.form['password']

        if user_id in DUMMY_USERS and DUMMY_USERS[user_id]['password'] == password:
            session['user_id'] = user_id
            flash('ログインに成功しました。', 'success')
            return redirect(url_for('home'))
        else:
            flash('ユーザーIDまたはパスワードが正しくありません。', 'danger')
            return render_template('login.html')

    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    """新規登録画面の表示 (GET) と 登録処理 (POST)"""
    if request.method == 'POST':
        email = request.form['email']
        user_id = request.form['user_id']
        password = request.form['password']

        if not user_id or not password or not email:
            flash('全ての項目を入力してください。', 'danger')
            return render_template('register.html')

        if user_id in DUMMY_USERS:
            flash('このユーザーIDは既に使われています。', 'danger')
            return render_template('register.html')

        DUMMY_USERS[user_id] = {"password": password, "email": email}
        flash('新規登録が完了しました。ログインしてください。', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/home')
def home():
    """ログイン後のホーム画面"""
    if 'user_id' not in session:
        flash('このページにアクセスするにはログインが必要です。', 'warning')
        return redirect(url_for('login'))

    user_id = session['user_id']
    user_email = DUMMY_USERS[user_id]['email']
    return render_template('home.html', user_id=user_id, email=user_email)


# --- 安否確認・支援要請 ---

@app.route('/safety_check')
def safety_check():
    """安否確認・支援要請画面"""
    if 'user_id' not in session:
        flash('このページにアクセスするにはログインが必要です。', 'warning')
        return redirect(url_for('login'))

    return render_template('safety_check.html',
                           requests=reversed(SUPPORT_REQUESTS),
                           safety_checks=SAFETY_CHECKS.values())


@app.route('/submit_request', methods=['POST'])
def submit_request():
    """支援要請の処理"""
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    now = datetime.datetime.now().strftime('%Y/%m/%d %H:%M')

    new_request = {
        "user_id": user_id,
        "email": DUMMY_USERS.get(user_id, {}).get("email", "不明"),
        "category": request.form['category'],
        "priority": request.form['priority'],
        "details": request.form['details'],
        "timestamp": now
    }
    SUPPORT_REQUESTS.append(new_request)

    flash('支援要請を送信しました。', 'success')
    return redirect(url_for('safety_check'))


@app.route('/submit_safety_check', methods=['POST'])
def submit_safety_check():
    """安否報告の処理"""
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    now = datetime.datetime.now().strftime('%Y/%m/%d %H:%M')

    SAFETY_CHECKS[user_id] = {
        "user_id": user_id,
        "email": DUMMY_USERS.get(user_id, {}).get("email", "不明"),
        "status": "無事",
        "timestamp": now
    }

    flash(f"{session['user_id']} さんの安否を「無事」として報告しました。", 'success')
    return redirect(url_for('safety_check'))


# --- メインメニュー ---

@app.route('/menu')
def menu():
    """メインメニュー画面"""
    if 'user_id' not in session:
        flash('このページにアクセスするにはログインが必要です。', 'warning')
        return redirect(url_for('login'))

    return render_template('menu.html')


# --- チャット機能 ---

@app.route('/chat')
def chat():
    """チャット グループ選択画面"""
    if 'user_id' not in session:
        return redirect(url_for('login'))

    return render_template('chat.html', groups=DUMMY_GROUPS)


@app.route('/chat/<group_id>', methods=['GET', 'POST'])
def chat_room(group_id):
    """チャットルーム（メッセージ送受信）画面"""
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if group_id not in DUMMY_GROUPS:
        flash('存在しないグループです。', 'danger')
        return redirect(url_for('chat'))

    group_name = DUMMY_GROUPS[group_id]
    messages = CHAT_MESSAGES.get(group_id, [])

    if request.method == 'POST':
        text = request.form['message_text']
        if text:
            user_id = session['user_id']
            now = datetime.datetime.now().strftime('%Y/%m/%d %H:%M')

            new_message = {
                "user_id": user_id,
                "text": text,
                "timestamp": now
            }
            CHAT_MESSAGES[group_id].append(new_message)

        return redirect(url_for('chat_room', group_id=group_id))

    return render_template('chat_room.html',
                           group_name=group_name,
                           group_id=group_id,
                           messages=messages,
                           current_user_id=session['user_id'])


# --- ▼▼▼ コミュニティ機能（ダミーから本実装に変更） ▼▼▼ ---

@app.route('/community', methods=['GET', 'POST'])
def community():
    """コミュニティ（掲示板）機能"""
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        # 新規投稿の処理
        title = request.form['title']
        content = request.form['content']
        user_id = session['user_id']
        now = datetime.datetime.now().strftime('%Y/%m/%d %H:%M')

        if title and content:  # 件名と本文が空でないことを確認
            new_post = {
                "user_id": user_id,
                "title": title,
                "content": content,
                "timestamp": now
            }
            # リストの先頭に追加 (
            COMMUNITY_POSTS.insert(0, new_post)
            flash('新しい投稿を行いました。', 'success')
        else:
            flash('件名と本文の両方を入力してください。', 'danger')

        # 投稿後は、同じページにリダイレクトしてフォームの再送信を防ぐ
        return redirect(url_for('community'))

    # GETリクエストの場合（画面表示）
    # 保存されている投稿リストをテンプレートに渡す
    return render_template('community.html', posts=COMMUNITY_POSTS)


# --- メニュー（ダミー） ---
@app.route('/group_management')
def group_management():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    flash('「グループ管理」機能は現在準備中です。', 'info')
    return redirect(url_for('menu'))


@app.route('/qr_code')
def qr_code():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    flash('「QRコード」機能は現在準備中です。', 'info')
    return redirect(url_for('menu'))


@app.route('/settings')
def settings():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    flash('「設定」機能は現在準備中です。', 'info')
    return redirect(url_for('menu'))


# --- ★★★ 緊急SOS ★★★ ---

@app.route('/emergency_sos')
def emergency_sos():
    """緊急SOS発信画面の表示"""
    if 'user_id' not in session:
        flash('このページにアクセスするにはログインが必要です。', 'warning')
        return redirect(url_for('login'))

    # emergency_sos.html をレンダリング
    return render_template('emergency_sos.html')


@app.route('/submit_sos', methods=['POST'])
def submit_sos():
    """緊急SOSの処理"""
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    now = datetime.datetime.now().strftime('%Y/%m/%d %H:%M')

    # 新しいSOSレポートを作成
    new_sos_report = {
        "user_id": user_id,
        "email": DUMMY_USERS.get(user_id, {}).get("email", "不明"),
        "timestamp": now,
        "message": "緊急SOSが発信されました"
        # 注：実際のアプリではここで位置情報を取得するロジックが必要です
    }
    SOS_REPORTS.append(new_sos_report)
    # print(SOS_REPORTS) # (コンソールでの確認用)

    flash('緊急SOSを発信しました。管理者に通知されました。', 'danger')

    # ★★★ ここを変更しました ★★★
    # ホームではなく、SOS画面にリダイレクトします
    return redirect(url_for('emergency_sos'))


# --- ログアウト ---
@app.route('/logout')
def logout():
    """ログアウト処理"""
    session.pop('user_id', None)
    flash('ログアウトしました。', 'info')
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(debug=True)