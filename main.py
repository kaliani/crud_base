from fastapi import FastAPI, Request, Query
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
import asyncpg
from typing import Optional
from dotenv import load_dotenv
import os

from agent.graph import graph
from constants import INSTANCE_LABELS, REGION_LABELS

load_dotenv()

DATABASE_URL = (
    f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
    f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
)

app = FastAPI()
templates = Jinja2Templates(directory="templates")


async def get_db():
    return await asyncpg.connect(DATABASE_URL)


def to_int(value: Optional[str]) -> Optional[int]:
    try:
        return int(value) if value not in (None, "") else None
    except (ValueError, TypeError):
        return None


@app.post("/chat")
async def chat(request: Request):
    body = await request.json()
    question = body.get("question", "").strip()
    if not question:
        return JSONResponse({"answer": ""}, status_code=400)
    try:
        result = await graph.ainvoke({
            "messages": [{"role": "user", "content": question}]
        })
        answer = result["messages"][-1].content
    except Exception as e:
        return JSONResponse({"answer": f"Помилка: {e}"}, status_code=500)
    return {"answer": answer}


@app.get("/judges", response_class=HTMLResponse)
async def judges(
    request: Request,
    search: Optional[str] = Query(default=None),
    court_code: Optional[str] = Query(default=None),
):
    court_code_int = to_int(court_code)
    conn = await get_db()
    try:
        conditions = []
        params = []

        if search:
            params.append(f"%{search}%")
            conditions.append(f"LOWER(j.name) LIKE LOWER(${len(params)})")

        if court_code_int is not None:
            params.append(court_code_int)
            conditions.append(f"j.court_code = ${len(params)}")

        where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        query = (
            f"SELECT j.dos_id, j.name, j.short_name, j.last_name, j.first_name, j.patronymic, "
            f"j.sex, j.court_code, c.name AS court_name "
            f"FROM public.new_judges j "
            f"LEFT JOIN public.courts c ON j.court_code = c.court_code "
            f"{where} ORDER BY j.last_name, j.first_name"
        )

        rows = await conn.fetch(query, *params)
        judges_list = [dict(r) for r in rows]

        courts_rows = await conn.fetch(
            "SELECT DISTINCT j.court_code, c.name FROM public.new_judges j "
            "LEFT JOIN public.courts c ON j.court_code = c.court_code ORDER BY c.name"
        )
        courts_for_filter = [dict(r) for r in courts_rows]
    finally:
        await conn.close()

    return templates.TemplateResponse(request, "judges.html", {
        "judges": judges_list,
        "total": len(judges_list),
        "search": search or "",
        "selected_court_code": court_code_int,
        "courts_for_filter": courts_for_filter,
    })


@app.get("/", response_class=HTMLResponse)
async def index(
    request: Request,
    search: Optional[str] = Query(default=None),
    instance_code: Optional[str] = Query(default=None),
    region_code: Optional[str] = Query(default=None),
    court_code: Optional[str] = Query(default=None),
):
    instance_code = to_int(instance_code)
    region_code = to_int(region_code)
    court_code = to_int(court_code)
    conn = await get_db()
    try:
        conditions = []
        params = []

        if search:
            params.append(f"%{search}%")
            conditions.append(f"LOWER(name) LIKE LOWER(${len(params)})")

        if instance_code is not None:
            params.append(instance_code)
            conditions.append(f"instance_code = ${len(params)}")

        if region_code is not None:
            params.append(region_code)
            conditions.append(f"region_code = ${len(params)}")

        if court_code is not None:
            params.append(court_code)
            conditions.append(f"court_code = ${len(params)}")

        where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        query = f"SELECT court_code, name, instance_code, region_code FROM public.courts {where} ORDER BY name"

        rows = await conn.fetch(query, *params)
        courts = [dict(r) for r in rows]

        instance_codes = await conn.fetch("SELECT DISTINCT instance_code FROM public.courts ORDER BY instance_code")
        region_codes = await conn.fetch("SELECT DISTINCT region_code FROM public.courts ORDER BY region_code")
    finally:
        await conn.close()

    return templates.TemplateResponse(request, "index.html", {
        "courts": courts,
        "total": len(courts),
        "search": search or "",
        "selected_instance": instance_code,
        "selected_region": region_code,
        "selected_court_code": court_code,
        "instance_codes": [r["instance_code"] for r in instance_codes],
        "region_codes": [r["region_code"] for r in region_codes],
        "instance_labels": INSTANCE_LABELS,
        "region_labels": REGION_LABELS,
    })
