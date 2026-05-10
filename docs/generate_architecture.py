"""Contract-Guard 아키텍처 다이어그램 (AWS 스타일).

PIL만 사용. 컴포넌트는 색상 아이콘 + 라벨, 그룹은 점선 컨테이너로 표현.
"""
import math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

OUTPUT = Path(__file__).parent / "architecture.png"

W, H = 1900, 1320
BG = (252, 252, 250)

# 그룹/카테고리 색상 (AWS 스타일에서 따옴)
C_USER = (90, 90, 100)
C_BROWSER = (52, 120, 200)

C_FRONT = (33, 110, 161)            # 파랑 (React)
C_FRONT_BG = (217, 234, 247)
C_FRONT_DASH = (33, 110, 161)

C_API = (217, 119, 6)               # 주황 (FastAPI 엔드포인트)
C_API_BG = (253, 234, 209)

C_SVC = (62, 122, 88)               # 그린 (서비스)
C_SVC_BG = (220, 236, 226)

C_RAG = (138, 78, 162)              # 퍼플 (RAG)
C_RAG_BG = (236, 224, 242)

C_DATA = (179, 100, 60)             # 브론즈 (데이터)
C_DATA_BG = (245, 224, 211)

C_EXT = (210, 64, 64)               # 빨강 (외부 LLM/임베딩)
C_EXT_BG = (250, 224, 224)

C_BACKEND_DASH = (180, 130, 50)     # 백엔드 컨테이너 점선

C_LINE = (110, 110, 120)
C_LINE_LIGHT = (170, 170, 180)
C_TEXT = (32, 32, 40)
C_LABEL = (90, 90, 100)
C_TITLE = (20, 20, 28)

FONT_PATH = "C:/Windows/Fonts/malgun.ttf"
FONT_BOLD_PATH = "C:/Windows/Fonts/malgunbd.ttf"


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(FONT_BOLD_PATH if bold else FONT_PATH, size)


def text_size(draw, text, fnt):
    bbox = draw.textbbox((0, 0), text, font=fnt)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]


def text_centered(draw, cx, y, text, fnt, fill=C_TEXT):
    w, _ = text_size(draw, text, fnt)
    draw.text((cx - w / 2, y), text, font=fnt, fill=fill)


# -----------------------------------------------------------------------------
# 점선 그리기 유틸 (PIL은 점선 미지원이라 직접 그림)
# -----------------------------------------------------------------------------
def dashed_line(draw, x1, y1, x2, y2, color, width=2, dash=8, gap=6):
    dx, dy = x2 - x1, y2 - y1
    length = math.hypot(dx, dy)
    if length == 0:
        return
    ux, uy = dx / length, dy / length
    pos = 0
    while pos < length:
        end = min(pos + dash, length)
        sx, sy = x1 + ux * pos, y1 + uy * pos
        ex, ey = x1 + ux * end, y1 + uy * end
        draw.line([sx, sy, ex, ey], fill=color, width=width)
        pos += dash + gap


def dashed_rounded_rect(draw, x, y, w, h, color, width=2, radius=18):
    # 4개의 직선 + 4개의 모서리 호 (호는 실선으로 — 점선 호는 보기 안좋음)
    dashed_line(draw, x + radius, y, x + w - radius, y, color, width)
    dashed_line(draw, x + radius, y + h, x + w - radius, y + h, color, width)
    dashed_line(draw, x, y + radius, x, y + h - radius, color, width)
    dashed_line(draw, x + w, y + radius, x + w, y + h - radius, color, width)
    # 모서리 호
    draw.arc([x, y, x + 2 * radius, y + 2 * radius], 180, 270, fill=color, width=width)
    draw.arc([x + w - 2 * radius, y, x + w, y + 2 * radius], 270, 360, fill=color, width=width)
    draw.arc([x, y + h - 2 * radius, x + 2 * radius, y + h], 90, 180, fill=color, width=width)
    draw.arc([x + w - 2 * radius, y + h - 2 * radius, x + w, y + h], 0, 90, fill=color, width=width)


# -----------------------------------------------------------------------------
# 화살표
# -----------------------------------------------------------------------------
def arrow(draw, x1, y1, x2, y2, color=C_LINE, width=2, head=11):
    draw.line([x1, y1, x2, y2], fill=color, width=width)
    angle = math.atan2(y2 - y1, x2 - x1)
    px = x2 - head * math.cos(angle)
    py = y2 - head * math.sin(angle)
    left = (px + head * 0.55 * math.cos(angle + math.pi / 2),
            py + head * 0.55 * math.sin(angle + math.pi / 2))
    right = (px + head * 0.55 * math.cos(angle - math.pi / 2),
             py + head * 0.55 * math.sin(angle - math.pi / 2))
    draw.polygon([(x2, y2), left, right], fill=color)


def edge_label(draw, x, y, text, color=C_LABEL):
    f = font(11)
    w, h = text_size(draw, text, f)
    pad = 5
    draw.rectangle([x - w / 2 - pad, y - h / 2 - 2, x + w / 2 + pad, y + h / 2 + 4],
                   fill=BG)
    draw.text((x - w / 2, y - h / 2), text, font=f, fill=color)


# -----------------------------------------------------------------------------
# 아이콘 헬퍼 — 각 컴포넌트는 (icon + label) 한 쌍으로 표현
# 모두 cx, cy 중심 + size 인자
# -----------------------------------------------------------------------------
def icon_box(draw, cx, cy, size, color, label, sublabel=None):
    """컴포넌트 박스 (라운드 사각형 + 아이콘 라벨 글자)."""
    s = size
    rounded_rectangle(draw, cx - s / 2, cy - s / 2, s, s,
                      fill=color, outline=color, radius=10)
    f = font(11, bold=True)
    text_centered(draw, cx, cy + s / 2 + 6, label, font(11, bold=True))
    if sublabel:
        text_centered(draw, cx, cy + s / 2 + 22, sublabel, font(10), fill=C_LABEL)


def rounded_rectangle(draw, x, y, w, h, fill, outline, radius=10, width=2):
    draw.rounded_rectangle([x, y, x + w, y + h], radius=radius,
                           fill=fill, outline=outline, width=width)


def icon_user(draw, cx, cy, size, color):
    """사람 아이콘 (머리 + 몸통)."""
    head_r = size * 0.18
    draw.ellipse([cx - head_r, cy - size / 2, cx + head_r, cy - size / 2 + 2 * head_r],
                 fill=color, outline=color)
    body_top = cy - size / 2 + 2 * head_r + 2
    body_w = size * 0.7
    draw.pieslice([cx - body_w / 2, body_top, cx + body_w / 2, body_top + body_w],
                  start=180, end=360, fill=color, outline=color)


def icon_browser(draw, cx, cy, size, color):
    s = size
    x, y = cx - s / 2, cy - s / 2
    draw.rounded_rectangle([x, y, x + s, y + s], radius=6, fill=color)
    # 타이틀바
    draw.rectangle([x, y, x + s, y + s * 0.22], fill=(255, 255, 255, 0))
    bar_color = (255, 255, 255)
    draw.rectangle([x + 4, y + 4, x + s - 4, y + s * 0.22 - 2], fill=bar_color)
    # 신호등 점 3개
    for i in range(3):
        dx = x + 8 + i * 9
        dy = y + s * 0.11
        draw.ellipse([dx - 3, dy - 3, dx + 3, dy + 3], fill=color)


def icon_server(draw, cx, cy, size, color):
    """서버 랙 아이콘."""
    s = size
    x, y = cx - s / 2, cy - s / 2
    draw.rounded_rectangle([x, y, x + s, y + s], radius=6, fill=color)
    # 가로 줄 3개 (랙 슬롯)
    line = (255, 255, 255)
    for i in range(3):
        ly = y + s * (0.25 + 0.22 * i)
        draw.rectangle([x + 8, ly, x + s - 8, ly + 4], fill=line)
        # LED
        draw.ellipse([x + s - 14, ly + 1, x + s - 9, ly + 6], fill=(120, 240, 120))


def icon_db(draw, cx, cy, size, color):
    """데이터베이스 실린더."""
    s = size
    x, y = cx - s / 2, cy - s / 2
    rx = s / 2
    ry = s * 0.13
    body_top = y + ry
    body_bot = y + s - ry
    # 본체
    draw.rectangle([cx - rx, body_top, cx + rx, body_bot], fill=color)
    # 위 타원
    draw.ellipse([cx - rx, y, cx + rx, y + 2 * ry], fill=color, outline=(255, 255, 255), width=2)
    # 아래 타원
    draw.ellipse([cx - rx, body_bot - ry, cx + rx, body_bot + ry], fill=color)
    draw.arc([cx - rx, body_bot - ry, cx + rx, body_bot + ry], 0, 180, fill=(255, 255, 255), width=2)


def icon_doc(draw, cx, cy, size, color):
    """문서 아이콘 (모서리 접힘)."""
    s = size
    x, y = cx - s * 0.4, cy - s / 2
    fold = s * 0.22
    pts = [
        (x, y), (x + s * 0.8 - fold, y), (x + s * 0.8, y + fold),
        (x + s * 0.8, y + s), (x, y + s),
    ]
    draw.polygon(pts, fill=color)
    # 접힘
    draw.polygon([(x + s * 0.8 - fold, y),
                  (x + s * 0.8, y + fold),
                  (x + s * 0.8 - fold, y + fold)],
                 fill=(255, 255, 255))
    # 본문 줄
    for i in range(3):
        ly = y + fold + 8 + i * 8
        draw.rectangle([x + 6, ly, x + s * 0.8 - 8, ly + 3], fill=(255, 255, 255))


def icon_gear(draw, cx, cy, size, color):
    """톱니바퀴 — 서비스/처리 로직."""
    s = size
    r_outer = s / 2
    r_inner = s * 0.32
    teeth = 10
    pts = []
    for i in range(teeth * 2):
        a = i * math.pi / teeth - math.pi / 2
        r = r_outer if i % 2 == 0 else r_outer * 0.78
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    draw.polygon(pts, fill=color)
    # 중앙 구멍
    draw.ellipse([cx - r_inner, cy - r_inner, cx + r_inner, cy + r_inner],
                 fill=BG, outline=color, width=2)


def icon_cloud(draw, cx, cy, size, color):
    """구름 — 외부 모델/서비스."""
    s = size
    x, y = cx - s / 2, cy - s * 0.3
    draw.ellipse([x, y, x + s * 0.55, y + s * 0.55], fill=color)
    draw.ellipse([x + s * 0.25, y - s * 0.12, x + s * 0.75, y + s * 0.45], fill=color)
    draw.ellipse([x + s * 0.45, y, x + s, y + s * 0.55], fill=color)
    draw.rounded_rectangle([x + s * 0.05, y + s * 0.3, x + s * 0.95, y + s * 0.6],
                           radius=8, fill=color)


def icon_endpoint(draw, cx, cy, size, color):
    """API 엔드포인트 — 좌우 화살표가 있는 사각형."""
    s = size
    x, y = cx - s / 2, cy - s / 2
    draw.rounded_rectangle([x + s * 0.15, y + s * 0.2, x + s * 0.85, y + s * 0.8],
                           radius=6, fill=color)
    # 좌우 화살표
    arrow_h = s * 0.25
    # 왼쪽 들어오는 화살표
    draw.polygon([(x, cy), (x + s * 0.15, cy - arrow_h / 2), (x + s * 0.15, cy + arrow_h / 2)],
                 fill=color)
    # 오른쪽 나가는 화살표
    draw.polygon([(x + s, cy), (x + s * 0.85, cy - arrow_h / 2), (x + s * 0.85, cy + arrow_h / 2)],
                 fill=color)


def icon_brain(draw, cx, cy, size, color):
    """LLM/뇌 — 둥근 패턴이 있는 원."""
    s = size
    draw.ellipse([cx - s / 2, cy - s / 2, cx + s / 2, cy + s / 2], fill=color)
    # 노드 점들
    for ang in (0, 60, 120, 180, 240, 300):
        a = math.radians(ang)
        nx = cx + s * 0.28 * math.cos(a)
        ny = cy + s * 0.28 * math.sin(a)
        draw.ellipse([nx - 4, ny - 4, nx + 4, ny + 4], fill=(255, 255, 255))
    # 중심 점
    draw.ellipse([cx - 5, cy - 5, cx + 5, cy + 5], fill=(255, 255, 255))


# -----------------------------------------------------------------------------
# 컴포넌트: 아이콘 + 라벨 + 서브라벨
# -----------------------------------------------------------------------------
def component(draw, cx, cy, label, sublabel=None, *, icon_fn, color, size=58):
    icon_fn(draw, cx, cy, size, color)
    text_centered(draw, cx, cy + size / 2 + 8, label, font(11, bold=True))
    if sublabel:
        text_centered(draw, cx, cy + size / 2 + 24, sublabel, font(10), fill=C_LABEL)


def group(draw, x, y, w, h, title, color, *, title_bg=None):
    """점선 그룹 박스 + 좌상단 라벨."""
    dashed_rounded_rect(draw, x, y, w, h, color, width=2, radius=18)
    f = font(13, bold=True)
    tw, th = text_size(draw, title, f)
    pad_x, pad_y = 10, 5
    bg = title_bg or BG
    draw.rectangle([x + 18, y - th / 2 - pad_y, x + 18 + tw + pad_x * 2, y + th / 2 + pad_y],
                   fill=bg)
    draw.text((x + 18 + pad_x, y - th / 2), title, font=f, fill=color)


# =============================================================================
# 도화지 시작
# =============================================================================
img = Image.new("RGB", (W, H), BG)
draw = ImageDraw.Draw(img)

# ---- 타이틀 ----
draw.text((40, 24), "Contract-Guard 시스템 아키텍처",
          font=font(28, bold=True), fill=C_TITLE)
draw.text((40, 64),
          "RAG 기반 한국 계약서 위험 분석  ·  FastAPI + React + Ollama exaone3.5:7.8b",
          font=font(14), fill=(80, 80, 90))

# =============================================================================
# 사용자 (우측 상단)
# =============================================================================
component(draw, 1750, 110, "사용자", "Browser",
          icon_fn=icon_user, color=C_USER, size=64)

component(draw, 1750, 250, "웹 브라우저", "Vite Dev / Static",
          icon_fn=icon_browser, color=C_BROWSER, size=58)

# =============================================================================
# Frontend 그룹 (좌상단)
# =============================================================================
fx, fy, fw, fh = 60, 130, 1480, 200
group(draw, fx, fy, fw, fh, "Frontend  ·  React + Vite  (port 5173)", C_FRONT)

# 컴포넌트 4개
component(draw, fx + 130, fy + 90, "UploadPage",
          "홈 · KB 통계 · 업로드", icon_fn=icon_doc, color=C_FRONT, size=58)
component(draw, fx + 410, fy + 90, "ResultPage",
          "원문 · 분석 · 수정안 · Export", icon_fn=icon_doc, color=C_FRONT, size=58)
component(draw, fx + 690, fy + 90, "api/client.js",
          "axios · timeout 10m", icon_fn=icon_gear, color=C_FRONT, size=58)
component(draw, fx + 970, fy + 90, "components",
          "RiskBadge · Layout", icon_fn=icon_gear, color=C_FRONT, size=58)
component(draw, fx + 1250, fy + 90, "global.css",
          "테마 · 반응형", icon_fn=icon_gear, color=C_FRONT, size=58)

# 사용자 → Browser → Frontend
arrow(draw, 1750, 152, 1750, 218)
arrow(draw, 1715, 250, fx + fw + 6, fy + 90)
edge_label(draw, 1620, fy + 80, "HTTP")

# =============================================================================
# Backend 컨테이너 (큰 점선 박스 — API + Service + RAG 포함)
# =============================================================================
bx, by, bw, bh = 60, 380, 1780, 580
group(draw, bx, by, bw, bh,
      "Backend  ·  FastAPI  (port 8000)", C_BACKEND_DASH)

# ---- API 엔드포인트 행 ----
ay_row = by + 70
api_xs = [bx + 130, bx + 410, bx + 690, bx + 970, bx + 1250, bx + 1530]
api_specs = [
    ("POST /upload", "파일 → 분석"),
    ("GET /analyses/{id}", "결과 조회"),
    ("GET /export", "DOCX/PDF/HWPX"),
    ("GET /kb/status", "KB 통계"),
    ("GET /health", "Ollama 핑"),
    ("CORS · 미들웨어", "main.py"),
]
for cx, (label, sub) in zip(api_xs, api_specs):
    component(draw, cx, ay_row, label, sub,
              icon_fn=icon_endpoint, color=C_API, size=58)

# Frontend → API
arrow(draw, fx + 410, fy + fh - 10, api_xs[0], ay_row - 35)
edge_label(draw, fx + 540, fy + fh + 30, "JSON / multipart")

# ---- Service 레이어 ----
sy_row = by + 250
svc_xs = [bx + 110, bx + 320, bx + 540, bx + 760, bx + 980, bx + 1200, bx + 1430, bx + 1650]
svc_specs = [
    ("document_service", "PDF/DOCX/HWP 추출"),
    ("clause_service", "조항 · 갑/을 감지"),
    ("analysis_service ★", "오케스트레이터"),
    ("rewrite_service", "수정안 LLM"),
    ("export_service", "DOCX/PDF/HWPX"),
    ("rule_filter", "사전 룰 필터"),
    ("llm_service", "Ollama 래퍼"),
    ("embedding_service", "BGE-M3 래퍼"),
]
for cx, (label, sub) in zip(svc_xs, svc_specs):
    component(draw, cx, sy_row, label, sub,
              icon_fn=icon_gear, color=C_SVC, size=58)

# API → Service (대표 화살표)
arrow(draw, api_xs[0], ay_row + 42, svc_xs[0], sy_row - 35)
arrow(draw, api_xs[2], ay_row + 42, svc_xs[4], sy_row - 35)
arrow(draw, api_xs[1], ay_row + 42, svc_xs[2], sy_row - 35)

# analysis_service → rewrite_service
arrow(draw, svc_xs[2] + 35, sy_row, svc_xs[3] - 35, sy_row, color=C_SVC)
edge_label(draw, (svc_xs[2] + svc_xs[3]) / 2, sy_row - 10, "high/medium")

# ---- RAG 레이어 ----
ry_row = by + 440
rag_xs = [bx + 200, bx + 500, bx + 820, bx + 1140, bx + 1460]
rag_specs = [
    ("rag/chain.py", "분석 오케스트레이션"),
    ("rag/prompts.py", "유형별 프롬프트"),
    ("retrieval_service", "BM25 + Vector + RRF"),
    ("contract_types", "유형 메타 · 룰"),
    ("models (Pydantic)", "AnalysisResult 등"),
]
for cx, (label, sub) in zip(rag_xs, rag_specs):
    component(draw, cx, ry_row, label, sub,
              icon_fn=icon_brain, color=C_RAG, size=58)

# Service → RAG (대표)
arrow(draw, svc_xs[2], sy_row + 42, rag_xs[0], ry_row - 35)
edge_label(draw, (svc_xs[2] + rag_xs[0]) / 2, (sy_row + ry_row) / 2 - 4,
           "analyze_all_clauses")
arrow(draw, svc_xs[3], sy_row + 42, rag_xs[1], ry_row - 35)
arrow(draw, svc_xs[5], sy_row + 42, rag_xs[3], ry_row - 35)

# RAG 내부: chain → prompts / retrieval
arrow(draw, rag_xs[0] + 35, ry_row, rag_xs[1] - 35, ry_row, color=C_RAG)
arrow(draw, rag_xs[1] + 35, ry_row, rag_xs[2] - 35, ry_row, color=C_RAG)

# =============================================================================
# Data Layer (좌하단)
# =============================================================================
dx, dy, dw, dh = 60, 1010, 1100, 230
group(draw, dx, dy, dw, dh,
      "Data Storage  ·  Persistent Files", C_DATA)

data_xs = [dx + 130, dx + 350, dx + 580, dx + 800, dx + 990]
data_specs = [
    ("ChromaDB", "Vector · 188MB · 10,968 docs", icon_db),
    ("BM25 index", "63MB · contract_type 분리", icon_db),
    ("data/raw/laws/", "법률 11개 (legalize-kr)", icon_doc),
    ("data/raw/aihub/", "약관 · 판결문 JSON", icon_doc),
    ("data/results/", "분석 결과 JSON", icon_doc),
]
for cx, (label, sub, ic) in zip(data_xs, data_specs):
    component(draw, cx, dy + 90, label, sub,
              icon_fn=ic, color=C_DATA, size=58)

# RAG retrieval → ChromaDB / BM25
arrow(draw, rag_xs[2] - 30, ry_row + 35, data_xs[0], dy + 50)
edge_label(draw, (rag_xs[2] + data_xs[0]) / 2 - 60, dy + 30, "벡터 검색")
arrow(draw, rag_xs[2] + 30, ry_row + 35, data_xs[1], dy + 50)
edge_label(draw, (rag_xs[2] + data_xs[1]) / 2 + 30, dy + 30, "키워드 검색")

# analysis_service → results/
arrow(draw, svc_xs[2] - 20, sy_row + 42, data_xs[4] - 30, dy + 50, color=C_LINE_LIGHT)
edge_label(draw, data_xs[4] - 90, dy + 5, "save JSON")

# export_service → results/
arrow(draw, svc_xs[4], sy_row + 42, data_xs[4] + 30, dy + 50, color=C_LINE_LIGHT)
edge_label(draw, data_xs[4] + 90, dy + 5, "load JSON")

# build_kb 빌드 흐름 (raw → chroma + bm25)
arrow(draw, data_xs[2] - 30, dy + 90, data_xs[0] + 35, dy + 90,
      color=C_LINE_LIGHT, width=1)
arrow(draw, data_xs[3] - 30, dy + 90, data_xs[1] + 35, dy + 90,
      color=C_LINE_LIGHT, width=1)
edge_label(draw, (data_xs[1] + data_xs[2]) / 2, dy + 80,
           "build_kb.py", color=C_LINE_LIGHT)

# =============================================================================
# External Layer (우하단)
# =============================================================================
ex, ey, ew, eh = 1200, 1010, 640, 230
group(draw, ex, ey, ew, eh,
      "External Services", C_EXT)

component(draw, ex + 130, ey + 90, "Ollama", "exaone3.5:7.8b · port 11434",
          icon_fn=icon_cloud, color=C_EXT, size=64)
component(draw, ex + 330, ey + 90, "BGE-M3", "임베딩 1024d · HuggingFace",
          icon_fn=icon_cloud, color=C_EXT, size=64)
component(draw, ex + 530, ey + 90, "legalize-kr", "GitHub 법률 markdown",
          icon_fn=icon_cloud, color=C_EXT, size=64)

# llm_service → Ollama
arrow(draw, svc_xs[6], sy_row + 42, ex + 130, ey + 50)
edge_label(draw, (svc_xs[6] + ex + 130) / 2, (sy_row + ey) / 2 - 6, "LLM 호출")

# embedding_service → BGE-M3
arrow(draw, svc_xs[7], sy_row + 42, ex + 330, ey + 50)

# laws/raw 디렉토리 ← legalize-kr
arrow(draw, ex + 530, ey + 50, data_xs[2], dy + 130, color=C_LINE_LIGHT, width=1)
edge_label(draw, (ex + 530 + data_xs[2]) / 2, (ey + dy) / 2 + 80,
           "download_laws.py", color=C_LINE_LIGHT)

# =============================================================================
# 범례
# =============================================================================
ly = H - 36
legend_items = [
    (C_FRONT, "Frontend (React)"),
    (C_API, "API (FastAPI)"),
    (C_SVC, "Service Layer"),
    (C_RAG, "RAG Layer"),
    (C_DATA, "Data Storage"),
    (C_EXT, "External"),
]
lx = 40
for color, label in legend_items:
    draw.rounded_rectangle([lx, ly, lx + 18, ly + 18], radius=4, fill=color)
    f = font(11)
    draw.text((lx + 24, ly + 2), label, font=f, fill=C_TEXT)
    w, _ = text_size(draw, label, f)
    lx += 24 + w + 24

draw.text((40, H - 60),
          "★ analysis_service 가 메인 오케스트레이터 — 분석 + 수정안 생성 + JSON 영속화를 한 호출에 묶음",
          font=font(11), fill=(110, 110, 120))

img.save(OUTPUT, "PNG")
print(f"saved: {OUTPUT}  ({OUTPUT.stat().st_size // 1024} KB)")
