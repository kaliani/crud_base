from fastapi import FastAPI, Request, Query
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import asyncpg
from typing import Optional
from dotenv import load_dotenv
import os

load_dotenv()

app = FastAPI()
templates = Jinja2Templates(directory="templates")

DATABASE_URL = (
    f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
    f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
)

INSTANCE_LABELS = {
    1: "Перша інстанція (вищі суди)",
    2: "Апеляційна інстанція",
    3: "Перша інстанція (місцеві суди)",
}

REGION_LABELS = {
    1: "Вінницька",
    2: "Волинська",
    3: "Дніпропетровська",
    4: "Донецька",
    5: "Житомирська",
    6: "Закарпатська",
    7: "Запорізька",
    8: "Івано-Франківська",
    9: "Київська",
    10: "Кіровоградська",
    11: "Луганська",
    12: "Львівська",
    13: "Миколаївська",
    14: "Одеська",
    15: "Полтавська",
    16: "Рівненська",
    17: "Сумська",
    18: "Тернопільська",
    19: "Харківська",
    20: "Херсонська",
    21: "Хмельницька",
    22: "Черкаська",
    23: "Чернівецька",
    24: "Чернігівська",
    25: "АР Крим",
    26: "м. Київ",
    27: "м. Севастополь",
    31: "Луганська (окупована)",
    32: "Донецька (окупована)",
    33: "Запорізька (окупована)",
    34: "Херсонська (окупована)",
}


async def get_db():
    return await asyncpg.connect(DATABASE_URL)


def to_int(value: Optional[str]) -> Optional[int]:
    try:
        return int(value) if value not in (None, "") else None
    except (ValueError, TypeError):
        return None


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
