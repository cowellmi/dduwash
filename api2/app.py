from fastapi import FastAPI, Response
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import psycopg2
import os
import logging
from datetime import datetime, timezone
import pytz

logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("API_CORS")],
    allow_methods=["GET"],
    allow_headers=["*"],
)

def generate_html_table(rows):
    current_time_utc = datetime.now(timezone.utc)
    pst = pytz.timezone("America/Los_Angeles")
    current_time_pst = current_time_utc.astimezone(pst)
    iso_string = current_time_pst.isoformat()
    last_checked = current_time_pst.strftime("%-I:%M %p")

    tr = []
    for row in rows:
        tr.append(f"""
            <tr>
                <td>{row[1]}</td>
                <td>{row[2]}</td>
            </tr>
        """)
    
    return HTMLResponse(f"""
    <table>
        <caption>
            Last checked:
            <time datetime="{iso_string}">
                {last_checked}
            </time
        </caption>
        <thead>
            <tr>
                <th>Bay ID</th>
                <th>Status</th>
            </tr>
        </thead>
        <tbody>
            {"".join(tr)}
        </tbody>
    </table>
    """)

@app.get("/", response_class=HTMLResponse)
def get(response: Response):
    conn = None
    try:
        conn = psycopg2.connect(os.getenv("DATABASE_URL"))
        with conn.cursor() as cur:
            cur.execute("""
                SELECT DISTINCT ON (bay_id) time, bay_id, status_code
                FROM bay_status
                ORDER BY bay_id, time DESC;
            """)
            rows = cur.fetchall()
            return generate_html_table(rows)
    except Exception as e:
        logger.error(str(e))
        response.status_code = 204  # No Content
        return ""
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("API_PORT", "8080"))
    uvicorn.run(app, host="0.0.0.0", port=port)
