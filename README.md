# Basic Pitch API Server

音源からピッチ検出を行うAPIサーバー。TAB Editorで使用。

## セットアップ

```bash
# Python 3.11 必須（3.14だとbasic-pitchが動かない）
/opt/homebrew/bin/python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## 起動

```bash
# ポート8766で起動（Demucsは8765）
source venv/bin/activate
PORT=8766 python main.py
```

## ヘルスチェック

```bash
curl http://localhost:8766/
# {"status":"healthy","model_loaded":true}
```

## API

### POST /detect
URLから音源をダウンロードしてピッチ検出

```bash
curl -X POST http://localhost:8766/detect \
  -H "Content-Type: application/json" \
  -d '{"audio_url": "https://example.com/bass.mp3", "min_confidence": 0.5}'
```

### POST /detect-file
ファイルアップロードでピッチ検出

```bash
curl -X POST http://localhost:8766/detect-file \
  -F "file=@bass.mp3" \
  -F "min_confidence=0.5"
```

## TAB Editor との連携

環境変数 `BASIC_PITCH_API_URL` を設定:

```bash
BASIC_PITCH_API_URL=http://localhost:8766
```

Cloudflare Tunnel経由で公開する場合は、そのURLを設定。
