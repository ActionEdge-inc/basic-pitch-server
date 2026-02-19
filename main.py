"""
Basic Pitch API Server
音源からピッチ検出を行い、MIDIノート情報を返すAPIサーバー
"""

import os
import tempfile
from typing import Optional
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import httpx
import numpy as np

# Basic Pitchのインポート
from basic_pitch.inference import predict
from basic_pitch import ICASSP_2022_MODEL_PATH

app = FastAPI(
    title="Basic Pitch API",
    description="音源からピッチ検出を行うAPI",
    version="1.0.0"
)

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 本番では制限する
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# リクエスト/レスポンスモデル
class PitchRequest(BaseModel):
    audio_url: str
    min_confidence: Optional[float] = 0.5

class DetectedNote(BaseModel):
    time: float
    duration: float
    pitch: int
    confidence: float

class PitchResponse(BaseModel):
    success: bool
    notes: list[DetectedNote]
    note_count: int
    duration_seconds: float

class HealthResponse(BaseModel):
    status: str
    model_loaded: bool


@app.get("/", response_model=HealthResponse)
async def health_check():
    """ヘルスチェック"""
    return HealthResponse(
        status="healthy",
        model_loaded=True
    )


@app.post("/detect", response_model=PitchResponse)
async def detect_pitch(request: PitchRequest):
    """
    URLから音源をダウンロードしてピッチ検出を実行
    """
    try:
        # 音源をダウンロード
        async with httpx.AsyncClient() as client:
            response = await client.get(request.audio_url, timeout=60.0)
            if response.status_code != 200:
                raise HTTPException(
                    status_code=400,
                    detail=f"音源のダウンロードに失敗しました: {response.status_code}"
                )
            audio_data = response.content

        # 一時ファイルに保存
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp_file:
            tmp_file.write(audio_data)
            tmp_path = tmp_file.name

        try:
            # Basic Pitchで推論
            model_output, midi_data, note_events = predict(tmp_path)
            
            # note_eventsから情報を抽出
            # note_events: [(start_time, end_time, pitch, velocity, [pitch_bend]), ...]
            notes = []
            for event in note_events:
                start_time = event[0]
                end_time = event[1]
                pitch = int(event[2])
                velocity = event[3] / 127.0  # 0-127 を 0-1 に正規化（confidenceとして使用）
                
                if velocity >= request.min_confidence:
                    notes.append(DetectedNote(
                        time=round(start_time, 3),
                        duration=round(end_time - start_time, 3),
                        pitch=pitch,
                        confidence=round(velocity, 3)
                    ))
            
            # 音源の長さを推定
            duration = note_events[-1][1] if note_events else 0.0

            return PitchResponse(
                success=True,
                notes=notes,
                note_count=len(notes),
                duration_seconds=round(duration, 2)
            )

        finally:
            # 一時ファイルを削除
            os.unlink(tmp_path)

    except httpx.TimeoutException:
        raise HTTPException(status_code=408, detail="音源のダウンロードがタイムアウトしました")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ピッチ検出中にエラーが発生しました: {str(e)}")


@app.post("/detect-file", response_model=PitchResponse)
async def detect_pitch_from_file(
    file: UploadFile = File(...),
    min_confidence: float = 0.5
):
    """
    アップロードされた音源ファイルからピッチ検出を実行
    """
    try:
        # ファイル拡張子を取得
        ext = os.path.splitext(file.filename)[1] if file.filename else ".mp3"
        
        # 一時ファイルに保存
        with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_path = tmp_file.name

        try:
            # Basic Pitchで推論
            model_output, midi_data, note_events = predict(tmp_path)
            
            notes = []
            for event in note_events:
                start_time = event[0]
                end_time = event[1]
                pitch = int(event[2])
                velocity = event[3] / 127.0
                
                if velocity >= min_confidence:
                    notes.append(DetectedNote(
                        time=round(start_time, 3),
                        duration=round(end_time - start_time, 3),
                        pitch=pitch,
                        confidence=round(velocity, 3)
                    ))
            
            duration = note_events[-1][1] if note_events else 0.0

            return PitchResponse(
                success=True,
                notes=notes,
                note_count=len(notes),
                duration_seconds=round(duration, 2)
            )

        finally:
            os.unlink(tmp_path)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ピッチ検出中にエラーが発生しました: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
