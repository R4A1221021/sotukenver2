import os  # osモジュールをインポートします（シークレットキーの生成に使用）
from flask import Flask, render_template, request, redirect, url_for, session, flash  # Flask本体と、Web処理に必要な関数群をインポートします
import datetime  # タイムスタンプのために datetime をインポートします

# Flaskアプリケーションを初期化（インスタンスを作成）します
app = Flask(__name__)  # __name__ は現在のファイル名(app)を意味します

# セッション管理のためのシークレットキーを設定します（ログイン状態の維持に必須）
app.secret_key = os.urandom(24)  # os.urandom(24)で24バイトのランダムなキーを生成します

# --- ユーザーデータベース (ID, パスワード, メールアドレスを格納) ---
# 辞書型でダミーユーザーを定義します。キーはユーザーIDです。
DUMMY_USERS = {
    "user123": {"password": "password123", "email": "user@example.com"},  # ユーザーID "user123" の情報
    "admin": {"password": "adminpass", "email": "admin@example.com"}  # ユーザーID "admin" の情報
}  # 辞書の終わりです

# データベースの代わりにメモリ（グローバル変数）でデータを保持します
SUPPORT_REQUESTS = []  # 支援要請を格納するリスト
SAFETY_CHECKS = {}  # 安否確認を格納する辞書（ユーザーIDをキーにして最新情報を上書き）


# -------------------------------------------------------------------
# ルーティング関数
# -------------------------------------------------------------------

@app.route('/')  # ルートURL (例: http://127.0.0.1:5000/) にアクセスがあった場合の処理を定義します
def index():  # indexという名前の関数を定義します
    """ルートURL: ログイン状態に応じてリダイレクト"""
    if 'user_id' in session:  # もしセッション内に 'user_id' というキーが存在したら（＝ログイン済みなら）
        return redirect(url_for('home'))  # 'home'関数（/home）のURLへリダイレクト（転送）します
    else:  # そうでなければ（＝未ログインなら）
        return redirect(url_for('login'))  # 'login'関数（/login）のURLへリダイレクトします


@app.route('/login', methods=['GET', 'POST'])  # /login URLへのアクセスを定義します。GET（画面表示）とPOST（フォーム送信）を受け付けます
def login():  # loginという名前の関数を定義します
    """ログイン画面の表示 (GET) と ログイン処理 (POST)"""
    if 'user_id' in session:  # 既にログイン済みの場合は
        return redirect(url_for('home'))  # ホーム画面（/home）へリダイレクトします

    if request.method == 'POST':  # もしリクエストのメソッドが 'POST' だったら（＝ログインフォームが送信されたら）
        user_id = request.form['user_id']  # フォームデータから 'user_id' (ユーザーID)の値を取得します
        password = request.form['password']  # フォームデータから 'password' の値を取得します

        # 認証処理: ユーザーIDが存在し、パスワードが一致するか確認
        if user_id in DUMMY_USERS and DUMMY_USERS[user_id]['password'] == password:  # ユーザーIDが存在し、かつパスワードが一致したら
            # 認証成功
            session['user_id'] = user_id  # セッションにユーザーIDを保存します（これでログイン状態になります）
            flash('ログインに成功しました。', 'success')  # 'success'カテゴリでフラッシュメッセージ（成功通知）を設定します
            return redirect(url_for('home'))  # ホーム画面（/home）へリダイレクトします
        else:  # もし認証に失敗したら
            # 認証失敗
            flash('ユーザーIDまたはパスワードが正しくありません。', 'danger')  # 'danger'カテゴリでエラーメッセージを設定します
            return render_template('login.html')  # ログイン画面を再表示（エラーメッセージが表示される）

    return render_template('login.html')  # GETリクエストの場合、'login.html' テンプレートを読み込んで表示します


@app.route('/register', methods=['GET', 'POST'])  # /register URLへのアクセスを定義します
def register():  # registerという名前の関数を定義します
    """新規登録画面の表示 (GET) と 登録処理 (POST)"""
    if request.method == 'POST':  # もしリクエストのメソッドが 'POST' だったら（＝登録フォームが送信されたら）
        email = request.form['email']  # フォームからメールアドレスを取得
        user_id = request.form['user_id']  # フォームからユーザーIDを取得
        password = request.form['password']  # フォームからパスワードを取得

        # 簡易的なバリデーション
        if not user_id or not password or not email:  # どれか一つでも入力が空だったら
            flash('全ての項目を入力してください。', 'danger')  # エラーメッセージを設定
            return render_template('register.html')  # 登録画面を再表示

        # IDの重複チェック
        if user_id in DUMMY_USERS:  # もし入力されたユーザーIDが既に存在したら
            flash('このユーザーIDは既に使われています。', 'danger')  # エラーメッセージを設定
            return render_template('register.html')  # 登録画面を再表示

        # 新規ユーザーを登録（ダミーデータベースに追加）
        DUMMY_USERS[user_id] = {"password": password, "email": email}  # ユーザーIDをキーとして新しいユーザー情報を追加

        flash('新規登録が完了しました。ログインしてください。', 'success')  # 成功メッセージを設定
        return redirect(url_for('login'))  # ログイン画面へリダイレクト

    return render_template('register.html')  # GETリクエストの場合、'register.html' テンプレートを読み込んで表示します


@app.route('/home')  # /home URLへのアクセスを定義します
def home():  # homeという名前の関数を定義します
    """ログイン後のホーム画面"""
    if 'user_id' not in session:  # もしセッションに 'user_id' が存在しなかったら（＝未ログインなら）
        flash('このページにアクセスするにはログインが必要です。', 'warning')  # 警告メッセージを設定
        return redirect(url_for('login'))  # ログイン画面（/login）へリダイレクトします

    # ログイン済みの場合はホーム画面を表示
    user_id = session['user_id']  # セッションからユーザーIDを取得
    user_email = DUMMY_USERS[user_id]['email']  # ユーザーIDを使って、ダミーDBから登録メールアドレスを取得
    return render_template('home.html', user_id=user_id, email=user_email)  # 'home.html' を読み込み、IDとメールアドレスを渡します


# --- ここからが安否確認・支援要請の関数群です ---

@app.route('/safety_check')  # /safety_check URLへのアクセスを定義します
def safety_check():
    """安否確認・支援要請画面"""
    if 'user_id' not in session:  # もしセッションに 'user_id' が存在しなかったら（＝未ログインなら）
        flash('このページにアクセスするにはログインが必要です。', 'warning')  # 警告メッセージを設定
        return redirect(url_for('login'))  # ログイン画面（/login）へリダイレクトします

    # 保存されたデータをテンプレートに渡します
    # （リストを逆順[.reverse()]にすると、新しい順で表示できます）
    return render_template('safety_check.html',
                           requests=reversed(SUPPORT_REQUESTS),
                           safety_checks=SAFETY_CHECKS.values())


@app.route('/submit_request', methods=['POST'])  # 支援要請フォームのPOST処理
def submit_request():
    """支援要請の処理（ダミーではなくデータを保存）"""
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']

    ### 変更点: .now(datetime.timezone.utc) から .now() に変更し、ローカル時刻を取得 ###
    now = datetime.datetime.now().strftime('%Y/%m/%d %H:%M')  # 現在時刻 (ローカル)

    # フォームからデータを取得
    new_request = {
        "user_id": user_id,
        "email": DUMMY_USERS.get(user_id, {}).get("email", "不明"),  # ユーザー情報からEmailを取得
        "category": request.form['category'],
        "priority": request.form['priority'],
        "details": request.form['details'],
        "timestamp": now
    }

    # グローバル変数のリストに追加
    SUPPORT_REQUESTS.append(new_request)

    flash('支援要請を送信しました。', 'success')  # 成功メッセージを設定
    return redirect(url_for('safety_check'))  # 安否確認画面にリダイレクト


@app.route('/submit_safety_check', methods=['POST'])  # 安否報告フォームのPOST処理
def submit_safety_check():
    """安否報告の処理（ダミーではなくデータを保存）"""
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']

    ### 変更点: .now(datetime.timezone.utc) から .now() に変更し、ローカル時刻を取得 ###
    now = datetime.datetime.now().strftime('%Y/%m/%d %H:%M')  # 現在時刻 (ローカル)

    # 辞書にユーザーIDをキーとして保存（同じ人が再度押したら時間が更新される）
    SAFETY_CHECKS[user_id] = {
        "user_id": user_id,
        "email": DUMMY_USERS.get(user_id, {}).get("email", "不明"),
        "status": "無事",
        "timestamp": now
    }

    flash(f"{session['user_id']} さんの安否を「無事」として報告しました。", 'success')  # 成功メッセージを設定
    return redirect(url_for('safety_check'))  # 安否確認画面にリダイレクト


# --- ここまでが安否確認・支援要Scrape richiesta di
# ---


@app.route('/logout')  # /logout URLへのアクセスを定義します
def logout():  # logoutという名前の関数を定義します
    """ログアウト処理"""
    session.pop('user_id', None)  # セッションから 'user_id' を削除します
    flash('ログアウトしました。', 'info')  # 'info'カテゴリでお知らせメッセージを設定します
    return redirect(url_for('login'))  # ログイン画面（/login）へリダイレクトします


if __name__ == '__main__':  # もしこのファイル(app.py)が直接実行されたら
    app.run(debug=True)  # Flaskのテスト用サーバーをデバッグモードで起動します