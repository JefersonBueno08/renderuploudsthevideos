from __future__ import annotations

import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from celery import shared_task
from sqlalchemy.orm import Session

from backend.app.db import Base, SessionLocal, engine
from backend.app.models import Asset, AssetKind, Production, Status
from backend.app.settings import settings


def _db() -> Session:
    # garante schema em ambiente "worker-only"
    Base.metadata.create_all(bind=engine)
    return SessionLocal()


def _prod_dir(production_id: int) -> Path:
    root = Path(settings.storage_dir)
    d = root / "productions" / str(production_id)
    d.mkdir(parents=True, exist_ok=True)
    return d


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, retry_jitter=True, max_retries=5)
def generate_script(self, production_id: int) -> dict:
    db = _db()
    try:
        prod = db.get(Production, production_id)
        if not prod:
            raise RuntimeError(f"production {production_id} not found")
        prod.status = Status.running
        db.commit()

        # MVP: roteiro placeholder. Na etapa seguinte você pluga coleta/cluster + LLM/template.
        script = {
            "title": f"Notícias - {datetime.now(timezone.utc).strftime('%Y-%m-%d')}",
            "lines": [
                "Principais manchetes de agora.",
                "Resumo rápido e direto ao ponto.",
                "Fontes na descrição.",
            ],
        }

        out_dir = _prod_dir(production_id)
        script_path = out_dir / "script.json"
        script_path.write_text(json.dumps(script, ensure_ascii=False, indent=2), encoding="utf-8")

        db.add(Asset(production_id=production_id, kind=AssetKind.script, path=str(script_path)))
        db.commit()
        return {"script_path": str(script_path)}
    finally:
        db.close()


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, retry_jitter=True, max_retries=5)
def render_video(self, production_id: int) -> dict:
    db = _db()
    try:
        prod = db.get(Production, production_id)
        if not prod:
            raise RuntimeError(f"production {production_id} not found")

        out_dir = _prod_dir(production_id)
        video_path = out_dir / "final.mp4"

        # MVP: gera um vídeo base preto com texto (sem TTS ainda).
        # Isso garante que o pipeline de render + upload tenha um artefato válido.
        title = f"NEWS {production_id}"
        cmd = [
            "ffmpeg",
            "-y",
            "-f",
            "lavfi",
            "-i",
            "color=c=black:s=1080x1920:d=20",
            "-vf",
            f"drawtext=fontcolor=white:fontsize=64:x=(w-text_w)/2:y=(h-text_h)/2:text='{title}'",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            str(video_path),
        ]
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        db.add(Asset(production_id=production_id, kind=AssetKind.video, path=str(video_path)))
        prod.status = Status.succeeded
        db.commit()
        return {"video_path": str(video_path)}
    finally:
        db.close()


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, retry_jitter=True, max_retries=5)
def publish_youtube(self, production_id: int) -> dict:
    # Stub: ponto de integração YouTube Data API v3 (upload resumable + schedule).
    # Aqui você vai plugar OAuth2, quota handling e idempotência por production_id.
    out_dir = _prod_dir(production_id)
    video_path = out_dir / "final.mp4"
    if not video_path.exists():
        raise RuntimeError("render artifact missing")

    # Por enquanto, só "marca" que estaria pronto para upload.
    return {"ready": True, "video_path": str(video_path)}


@shared_task
def run_production(production_id: int) -> dict:
    # Pipeline linear MVP (depois vira DAG com branching por formato).
    s = generate_script.s(production_id)
    r = render_video.s(production_id)
    p = publish_youtube.s(production_id)
    chain_result = (s | r | p).apply_async()
    return {"task_id": chain_result.id}

