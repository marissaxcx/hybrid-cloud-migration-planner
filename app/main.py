from __future__ import annotations

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse

from app.planner import build_plan
from app.store import get_plan, list_plans, save_plan

app = FastAPI(title="Hybrid Cloud Migration Planner", version="1.0.0")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/plans", status_code=201)
def create_plan(payload: dict) -> dict:
    try:
        return save_plan(build_plan(payload))
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.get("/plans")
def plans(limit: int = Query(default=20, ge=1, le=100)) -> list[dict]:
    return list_plans(limit)


@app.get("/plans/{plan_id}")
def plan(plan_id: int) -> dict:
    result = get_plan(plan_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Plan not found")
    return result


@app.get("/", response_class=HTMLResponse)
def home() -> str:
    return """<!doctype html><html><head><meta charset='utf-8'><meta name='viewport' content='width=device-width'><title>Cloud Atlas 🗺️</title><style>
    :root{--ink:#342943;--rose:#f6d7df;--sky:#d8eff8;--cream:#fffaf1;--lilac:#e8e0f8}*{box-sizing:border-box}body{margin:0;background:linear-gradient(140deg,var(--cream),var(--rose));color:var(--ink);font:16px system-ui,sans-serif}.wrap{max-width:1000px;margin:5vh auto;padding:24px}.card{background:#ffffffdf;border:1px solid white;border-radius:24px;padding:28px;box-shadow:0 18px 55px #63364c14}h1{font-size:clamp(2rem,5vw,3.4rem);margin:.2em 0}p{line-height:1.6}textarea{width:100%;min-height:260px;border:1px solid #ead0da;border-radius:14px;padding:16px;font:13px ui-monospace,monospace;background:#fffdf9;color:var(--ink)}button{margin-top:14px;border:0;border-radius:999px;background:var(--ink);color:white;padding:13px 20px;font-weight:700;cursor:pointer}.tag{display:inline-block;background:var(--sky);padding:6px 10px;border-radius:99px;font-size:.85rem}pre{white-space:pre-wrap;word-break:break-word;background:#342943;color:white;border-radius:14px;padding:18px;min-height:60px}</style></head><body><main class='wrap'><section class='card'><span class='tag'>🗺️ a softer route to the cloud</span><h1>Hybrid Cloud Migration Planner</h1><p>Paste a workload inventory to sketch dependency-aware migration waves and Azure landing-service starting points.</p><textarea id='inventory' placeholder='Paste inventory JSON'></textarea><button onclick='planIt()'>Map my migration ✨</button><h2>Your cloud atlas</h2><pre id='result'>Your plan will appear here.</pre></section></main><script>async function planIt(){const out=document.querySelector('#result');try{const data=JSON.parse(document.querySelector('#inventory').value);const res=await fetch('/plans',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)});const body=await res.json();out.textContent=JSON.stringify(body,null,2)}catch(e){out.textContent='Please paste a valid workload inventory JSON object.'}}</script></body></html>"""
