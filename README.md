# Django プロジェクト セットアップ手順

## 環境構築手順

### 1. Git リポジトリをクローン
```sh
git clone <リポジトリURL>
cd <プロジェクトフォルダ>
```

### 2. Python 仮想環境を作成
```sh
python -m venv venv
source venv/bin/activate  # Windows の場合は `venv\Scripts\activate`
```

### 3. 必要な依存関係をインストール
```sh
pip install -r requirements.txt
```

### 4. `.env` ファイルの作成
`StageGateReview` アプリディレクトリ内に `.env` ファイルを作成し、以下の内容を設定してください。

```
SECRET_KEY=<Djangoのシークレットキー>
GOOGLE_API_KEY=<Google Gemini APIキー>
```

### 5. Django のセットアップ
```sh
python manage.py makemigrations
python manage.py migrate
python manage.py collectstatic
```

### 6. 言語メッセージのコンパイル
```sh
django-admin compilemessages
```

### 7. 開発サーバーの起動
```sh
python manage.py runserver
```

これでプロジェクトのセットアップが完了です！

