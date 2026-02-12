import json
import re
import urllib.request
import urllib.error

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "qwen2.5:1.5b"

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

def main():
    session = {"state": "waiting_intent", "order_id": None}

    print("IM 工单机器人（输入 exit 退出）")
    print("你可以输入“我想查订单”开始\n")

    while True:
        user = input("你：").strip()
        if user.lower() in ("exit", "quit"):
            print("系统：已退出。")
            break

        # 状态1：等待用户表达意图
        if session["state"] == "waiting_intent":
            if any(k in user for k in ["查订单", "订单", "查询", "工单", "售后"]):
                session["state"] = "waiting_order_id"
                prompt = "你是客服机器人。请用非常简短的一句话，礼貌地让用户提供订单号（只输出一句话）。"
                print("系统：" + ollama_generate(prompt))
            else:
                print("系统：你可以说“我想查订单”，我会引导你提供订单号。")
            continue

        # 状态2：等待订单号（规则校验优先）
        if session["state"] == "waiting_order_id":
            order_id = extract_order_id(user)
            if not order_id:
                print("系统：看起来不像订单号，请发一串数字，例如：123456")
                continue

            session["order_id"] = order_id
            session["state"] = "done"

            prompt = f"你是客服机器人。请用一句话确认已收到订单号 {order_id}，并询问是否还需要帮助（只输出一句话）。"
            print("系统：" + ollama_generate(prompt))
            continue

        # 状态3：结束
        if session["state"] == "done":
            print("系统：流程已结束。输入“我想查订单”可重新开始，或输入 exit 退出。")
            if any(k in user for k in ["查订单", "订单", "查询", "工单", "售后"]):
                session["state"] = "waiting_order_id"
                session["order_id"] = None
                print("系统：请提供订单号（例如：123456）")
            continue

if __name__ == "__main__":
    main()
