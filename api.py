
import os
import json
import re
import time
import urllib.request
import urllib.error
from typing import Dict, Any

from fastapi import FastAPI
from pydantic import BaseModel

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "qwen2.5:1.5b"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_PATH = os.path.join(BASE_DIR, "chat_logs.jsonl")

app = FastAPI(title="IM Dialog Demo (Ollama)", version="0.1.0")
SESSIONS: Dict[str, Dict[str, Any]] = {}

def now_ms() -> int:
    return int(time.time() * 1000)

def ollama_generate(prompt: str, temperature: float = 0.2) -> str:
    payload = {
        "model": MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": temperature}
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        OLLAMA_URL, data=data, headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            out = json.loads(resp.read().decode("utf-8"))
            return out.get("response", "").strip()
    except urllib.error.URLError as e:
        return f"[ERROR] 无法连接到 Ollama：{e}"
    except Exception as e:
        return f"[ERROR] 调用失败：{e}"

def extract_order_id(text: str):
    m = re.search(r"\b(\d{4,12})\b", text)
    return m.group(1) if m else None

def get_session(session_id: str) -> Dict[str, Any]:
    if session_id not in SESSIONS:
        SESSIONS[session_id] = {"state": "waiting_intent", "order_id": None}
    return SESSIONS[session_id]

def handle_message(session: Dict[str, Any], user_msg: str) -> str:
    state = session["state"]

    if state == "waiting_intent":
        if any(k in user_msg for k in ["查订单", "订单", "查询", "工单", "售后"]):
            session["state"] = "waiting_order_id"
            prompt = "你是客服机器人。请用非常简短的一句话，礼貌地让用户提供订单号（只输出一句话）。"
            return ollama_generate(prompt)
        return "你可以说“我想查订单”，我会引导你提供订单号。"

    if state == "waiting_order_id":
        order_id = extract_order_id(user_msg)
        if not order_id:
            return "看起来不像订单号，请发一串数字，例如：123456"

        session["order_id"] = order_id
        session["state"] = "done"
        prompt = f"你是客服机器人。请用一句话确认已收到订单号 {order_id}，并询问是否还需要帮助（只输出一句话）。"
        return ollama_generate(prompt)

    if state == "done":
        if any(k in user_msg for k in ["查订单", "订单", "查询", "工单", "售后"]):
            session["state"] = "waiting_order_id"
            session["order_id"] = None
            return "请提供订单号（例如：123456）"
        return "流程已结束。输入“我想查订单”可重新开始。"

    session["state"] = "waiting_intent"
    session["order_id"] = None
    return "状态异常已重置。你可以输入“我想查订单”开始。"

class ChatReq(BaseModel):
    session_id: str
    message: str

@app.get("/health")
def health():
    return {"ok": True, "model": MODEL}

@app.post("/chat")
def chat(req: ChatReq):
    start = now_ms()
    session = get_session(req.session_id)
    reply = handle_message(session, req.message.strip())
    cost_ms = now_ms() - start

    # === 追加一行 JSONL 日志，方便追溯与做数据分析 ===
    log_item = {
        "ts_ms": now_ms(),
        "session_id": req.session_id,
        "state": session["state"],
        "order_id": session["order_id"],
        "user_message": req.message,
        "reply": reply,
        "latency_ms": cost_ms
    }
    try:
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_item, ensure_ascii=False) + "\n")
    except Exception:
        # 日志失败不影响主流程（真实系统也是这样做）
        pass

    return {
        "session_id": req.session_id,
        "state": session["state"],
        "order_id": session["order_id"],
        "reply": reply,
        "latency_ms": cost_ms
    }

@app.post("/reset/{session_id}")
def reset(session_id: str):
    SESSIONS.pop(session_id, None)
    return {"session_id": session_id, "reset": True}
