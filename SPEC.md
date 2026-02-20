# Basic Pitch API Server — 仕様書

> 音源からピッチ検出を行うAPIサーバー
> 最終更新: 2026-02-20

---

## 概要

Spotify の Basic Pitch モデルを使用して、音源ファイルからMIDIノート情報を抽出するAPIサーバー。
TAB Editor のAI TAB生成機能で使用。

---

## 技術スタック

| 項目 | 技術 |
|------|------|
| フレームワーク | FastAPI |
| ピッチ検出 | Basic Pitch (Spotify) |
| 音声処理 | ffmpeg, libsndfile |
| ホスティング | Render |
| コンテナ | Docker |

---

## API エンドポイント

### GET /
ヘルスチェック

**Response:**
```json
{
  "status": "healthy",
  "model_loaded": true
}
```

### POST /detect
URLから音源をダウンロードしてピッチ検出

**Request:**
```json
{
  "audio_url": "https://example.com/audio.mp3",
  "min_confidence": 0.5
}
```

**Response:**
```json
{
  "success": true,
  "notes": [
    {
      "time": 0.0,
      "duration": 0.5,
      "pitch": 60,
      "confidence": 0.85
    }
  ],
  "note_count": 32,
  "duration_seconds": 180.5
}
```

### POST /detect-file
アップロードされた音源ファイルからピッチ検出

**Request:** multipart/form-data
- `file`: 音源ファイル (MP3/WAV)
- `min_confidence`: 最小信頼度 (optional, default: 0.5)

**Response:** 同上

---

## デプロイ

### Render へのデプロイ

1. GitHubにリポジトリ作成
2. Render Dashboard → New → Web Service
3. GitHubリポジトリを接続
4. 設定:
   - Environment: Docker
   - Plan: Starter (無料枠)
5. Deploy

### ローカル実行

```bash
# 依存関係インストール
pip install -r requirements.txt

# サーバー起動
uvicorn main:app --reload
```

---

## TAB Editor との連携

TAB Editor の `/api/ai/generate-tab` から呼び出される。

```typescript
// tab-editor/src/lib/ai/basic-pitch-provider.ts
const response = await fetch('https://basic-pitch-api.onrender.com/detect', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    audio_url: separatedTrackUrl,
    min_confidence: 0.5
  })
});
```

---

## 環境変数

| 変数 | 必須 | 説明 |
|------|------|------|
| PORT | × | サーバーポート (default: 8000) |

---

## TODO

- [ ] **Renderにカード登録** → <https://dashboard.render.com/billing>
- [ ] Render Dashboard から手動でデプロイ、または API 経由でデプロイ（APIキーは別途管理）
- [ ] デプロイ後、TAB Editor に `BASIC_PITCH_API_URL` を設定

---

## 変更履歴

| 日付 | 内容 |
|------|------|
| 2026-02-20 | 初版作成 |
