# HireFlow AI

本地优先的招聘自动化工作台：消息解析、候选人管理、状态流转、Dashboard、分析、提醒、AI 日报/周报和 Excel/Markdown 导入导出。

## 本地运行

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
streamlit run app.py
```

默认使用 `data/hireflow.db`。设置 `DATABASE_URL` 为 PostgreSQL URL 即可切换线上数据库；业务代码只使用 SQLAlchemy。

## AI 模式

没有 `DEEPSEEK_API_KEY` 时自动使用模拟模式，可完整演示流程。配置 key 后会调用 DeepSeek Chat Completions API。

## 功能

- 消息粘贴/Markdown 导入，AI 提取候选人字段，人工确认后入库
- 候选人搜索、编辑、状态流转、跟进日期和备注
- Dashboard 指标、漏斗和来源分析
- 智能提醒、AI 日报/周报
- CSV/Excel 导入导出，Markdown 报告导出
- SQLite 本地 / PostgreSQL 线上、自动建表与演示数据

## Streamlit Community Cloud

将仓库连接到 Streamlit Community Cloud，在 Secrets 中配置 `DATABASE_URL` 和 `DEEPSEEK_API_KEY`。核心数据必须使用持久化 PostgreSQL，不依赖云端文件系统。

## 数据库迁移

Phase 1 已引入 Alembic。升级前请先备份数据库：

```bash
cp data/hireflow.db data/hireflow.db.backup
alembic upgrade head
alembic current
alembic check
```

如果迁移失败，保留原始数据库不动，停止应用并从备份文件恢复到新的工作副本后排查；不要直接覆盖原始生产数据。当前基线版本为 `20261111_0002`，会保留 V1 `candidates` 记录并新增 V2 基础表、查询索引和状态字典。
