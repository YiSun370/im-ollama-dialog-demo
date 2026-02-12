IM Dialog Demo (Ollama + FastAPI)



一个“可控对话”的 IM 工单引导 demo：用状态机控制流程，模型只负责生成友好话术。



====================

Features



Session 状态机：waiting\_intent -> waiting\_order\_id -> done



HTTP API：POST /chat 传 session\_id 保持上下文



本地大模型：Ollama + qwen2.5:1.5b



可观测性：chat\_logs.jsonl 记录每次请求（JSONL）



基础压测：bench.py 输出 avg/p50/p95



====================

Requirements



Windows 10/11



Python 3.12（推荐使用 py）



Ollama 已安装并运行



已拉取模型：ollama pull qwen2.5:1.5b



====================

Run



安装依赖：

py -m pip install fastapi uvicorn



启动服务：

py -m uvicorn api:app --reload --port 8000



====================

Test



健康检查：

curl http://127.0.0.1:8000/health



对话测试（同一个 session\_id 才能保持状态）：

curl -X POST http://127.0.0.1:8000/chat

&nbsp;-H "Content-Type: application/json" -d "{"session\_id":"u1","message":"我想查订单"}"

curl -X POST http://127.0.0.1:8000/chat

&nbsp;-H "Content-Type: application/json" -d "{"session\_id":"u1","message":"abc"}"

curl -X POST http://127.0.0.1:8000/chat

&nbsp;-H "Content-Type: application/json" -d "{"session\_id":"u1","message":"123456"}"



查看日志（Windows cmd 建议切到 UTF-8）：

chcp 65001

type chat\_logs.jsonl



====================

Benchmark



运行并发压测：

py bench.py



本次压测结果（你已经跑出来的）：

concurrency=5, requests=15, total\_time\_s=9.38

latency\_ms avg=2556.1, p50=3123, p95=5564, max=5564



====================

API Docs



服务启动后，在浏览器打开：

http://127.0.0.1:8000/docs



（这里会看到 Swagger UI，可直接点按钮测试 /chat 接口）

