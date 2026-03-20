#!/usr/bin/env python3
import argparse
import json
import os
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = [
    "https://www.googleapis.com/auth/presentations",
    "https://www.googleapis.com/auth/drive",
]
CONFIG_DIR = Path.home() / ".config" / "gog"
CLIENT_FILE = CONFIG_DIR / "oauth-client.json"
TOKEN_FILE = CONFIG_DIR / "slides-token.json"
THEME_FILE = Path(__file__).resolve().with_name('slides-theme.json')

DEFAULT_THEME = {
    "name": "consulting-clean",
    "background_rgb": [255, 255, 255],
    "primary_rgb": [13, 27, 62],
    "accent_rgb": [91, 155, 213],
    "neutral_rgb": [102, 102, 102],
    "font_family": "Arial",
    "title_pt": 24,
    "body_pt": 14,
}

TEMPLATES = {
    "insight": {"type": "insight", "layout": "title + bullets"},
    "problem-solution": {"type": "problem-solution", "layout": "two-column"},
    "roadmap": {"type": "roadmap", "layout": "process"},
    "data": {"type": "data", "layout": "title-and-chart"},
}


def load_theme():
    if THEME_FILE.exists():
        return json.loads(THEME_FILE.read_text())
    THEME_FILE.write_text(json.dumps(DEFAULT_THEME, indent=2) + "\n")
    return DEFAULT_THEME.copy()


def save_theme(theme):
    THEME_FILE.write_text(json.dumps(theme, indent=2) + "\n")


def manual_auth():
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
    flow = InstalledAppFlow.from_client_secrets_file(str(CLIENT_FILE), SCOPES)
    flow.redirect_uri = "http://localhost"
    auth_url, _ = flow.authorization_url(prompt="consent")
    print("Open this URL in your browser:\n")
    print(auth_url)
    print("\nAfter approving access, paste the FULL redirect URL here:")
    redirect_response = input().strip()
    flow.fetch_token(authorization_response=redirect_response)
    TOKEN_FILE.write_text(flow.credentials.to_json())
    print(f"Saved token to {TOKEN_FILE}")
    return flow.credentials


def load_creds():
    creds = None
    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            creds = manual_auth()
        TOKEN_FILE.write_text(creds.to_json())
    return creds


def slides_service():
    return build("slides", "v1", credentials=load_creds())


def rgb(theme_key):
    vals = load_theme()[theme_key]
    return {"red": vals[0] / 255.0, "green": vals[1] / 255.0, "blue": vals[2] / 255.0}


def page_size(presentation):
    size = presentation.get("pageSize", {})
    width = (size.get("width") or {}).get("magnitude", 720)
    height = (size.get("height") or {}).get("magnitude", 405)
    return width, height

    return {"red": vals[0] / 255.0, "green": vals[1] / 255.0, "blue": vals[2] / 255.0}


def auth():
    load_creds()
    print("Auth OK")


def create_presentation(title):
    service = slides_service()
    pres = service.presentations().create(body={"title": title}).execute()
    print(json.dumps({
        "presentationId": pres.get("presentationId"),
        "title": pres.get("title"),
        "slides": len(pres.get("slides", [])),
    }, indent=2))


def get_presentation(presentation_id):
    service = slides_service()
    pres = service.presentations().get(presentationId=presentation_id).execute()
    slides = []
    for s in pres.get("slides", []):
        slides.append({
            "objectId": s.get("objectId"),
            "pageElements": len(s.get("pageElements", [])),
        })
    print(json.dumps({
        "presentationId": pres.get("presentationId"),
        "title": pres.get("title"),
        "slides": slides,
        "theme": load_theme(),
    }, indent=2))


def _create_textbox_requests(object_id, x, y, w, h, text, font_pt, color_key="primary_rgb", bold=False):
    requests = [
        {
            "createShape": {
                "objectId": object_id,
                "shapeType": "TEXT_BOX",
                "elementProperties": {
                    "pageObjectId": None,
                    "size": {
                        "width": {"magnitude": w, "unit": "PT"},
                        "height": {"magnitude": h, "unit": "PT"},
                    },
                    "transform": {
                        "scaleX": 1,
                        "scaleY": 1,
                        "translateX": x,
                        "translateY": y,
                        "unit": "PT",
                    },
                },
            }
        },
        {"insertText": {"objectId": object_id, "text": text}},
        {
            "updateTextStyle": {
                "objectId": object_id,
                "style": {
                    "fontFamily": load_theme()["font_family"],
                    "fontSize": {"magnitude": font_pt, "unit": "PT"},
                    "foregroundColor": {"opaqueColor": {"rgbColor": rgb(color_key)}},
                    "bold": bold,
                },
                "textRange": {"type": "ALL"},
                "fields": "fontFamily,fontSize,foregroundColor,bold",
            }
        },
    ]
    return requests


def _create_slide(service, presentation_id, slide_id):
    service.presentations().batchUpdate(
        presentationId=presentation_id,
        body={"requests": [{"createSlide": {"objectId": slide_id, "slideLayoutReference": {"predefinedLayout": "BLANK"}}}]},
    ).execute()


def apply_theme(presentation_id):
    service = slides_service()
    pres = service.presentations().get(presentationId=presentation_id).execute()
    requests = []
    for slide in pres.get("slides", []):
        requests.append({
            "updatePageProperties": {
                "objectId": slide["objectId"],
                "pageProperties": {
                    "pageBackgroundFill": {
                        "solidFill": {"color": {"rgbColor": rgb("background_rgb")}}
                    }
                },
                "fields": "pageBackgroundFill.solidFill.color"
            }
        })
    service.presentations().batchUpdate(presentationId=presentation_id, body={"requests": requests}).execute()
    print(json.dumps({"presentationId": presentation_id, "theme_applied": load_theme()}, indent=2))


def set_font_style(font_family=None, title_pt=None, body_pt=None):
    theme = load_theme()
    if font_family:
        theme["font_family"] = font_family
    if title_pt is not None:
        theme["title_pt"] = title_pt
    if body_pt is not None:
        theme["body_pt"] = body_pt
    save_theme(theme)
    print(json.dumps(theme, indent=2))


def set_color_palette(primary_rgb=None, accent_rgb=None, neutral_rgb=None, background_rgb=None):
    theme = load_theme()
    if primary_rgb:
        theme["primary_rgb"] = primary_rgb
    if accent_rgb:
        theme["accent_rgb"] = accent_rgb
    if neutral_rgb:
        theme["neutral_rgb"] = neutral_rgb
    if background_rgb:
        theme["background_rgb"] = background_rgb
    save_theme(theme)
    print(json.dumps(theme, indent=2))


def add_title_slide(presentation_id, title_text, subtitle_text=""):
    service = slides_service()
    pres = service.presentations().get(presentationId=presentation_id).execute()
    slide_id = f"slide_{len(pres.get('slides', []))+1}"
    _create_slide(service, presentation_id, slide_id)
    requests = []
    requests += _create_textbox_requests("title_box_" + slide_id, 60, 80, 900, 80, title_text, load_theme()["title_pt"], bold=True)
    if subtitle_text:
        requests += _create_textbox_requests("subtitle_box_" + slide_id, 60, 170, 900, 50, subtitle_text, load_theme()["body_pt"], color_key="neutral_rgb")
    for req in requests:
        if 'createShape' in req:
            req['createShape']['elementProperties']['pageObjectId'] = slide_id
    service.presentations().batchUpdate(presentationId=presentation_id, body={"requests": requests}).execute()
    print(json.dumps({"presentationId": presentation_id, "createdSlideId": slide_id, "title": title_text, "subtitle": subtitle_text}, indent=2))


def create_two_column_slide(presentation_id, title, left_heading, left_bullets, right_heading, right_bullets):
    service = slides_service()
    pres = service.presentations().get(presentationId=presentation_id).execute()
    width, height = page_size(pres)
    margin_x = width * 0.06
    gutter = width * 0.04
    title_h = 60
    content_top = height * 0.22
    content_h = height * 0.60
    col_w = (width - (2 * margin_x) - gutter) / 2
    slide_id = f"slide_{len(pres.get('slides', []))+1}"
    _create_slide(service, presentation_id, slide_id)
    left_text = left_heading + "\n" + "\n".join(f"• {b}" for b in left_bullets[:5])
    right_text = right_heading + "\n" + "\n".join(f"• {b}" for b in right_bullets[:5])
    requests = []
    requests += _create_textbox_requests("title_box_" + slide_id, margin_x, height * 0.07, width - (2 * margin_x), title_h, title, load_theme()["title_pt"], bold=True)
    requests += _create_textbox_requests("left_box_" + slide_id, margin_x, content_top, col_w, content_h, left_text, load_theme()["body_pt"])
    requests += _create_textbox_requests("right_box_" + slide_id, margin_x + col_w + gutter, content_top, col_w, content_h, right_text, load_theme()["body_pt"])
    for req in requests:
        if 'createShape' in req:
            req['createShape']['elementProperties']['pageObjectId'] = slide_id
    service.presentations().batchUpdate(presentationId=presentation_id, body={"requests": requests}).execute()
    print(json.dumps({"presentationId": presentation_id, "createdSlideId": slide_id, "type": "two-column"}, indent=2))


def create_title_and_chart_slide(presentation_id, title, insight, chart_note="Chart placeholder"):
    service = slides_service()
    pres = service.presentations().get(presentationId=presentation_id).execute()
    slide_id = f"slide_{len(pres.get('slides', []))+1}"
    _create_slide(service, presentation_id, slide_id)
    requests = []
    requests += _create_textbox_requests("title_box_" + slide_id, 40, 30, 1040, 60, title, load_theme()["title_pt"], bold=True)
    requests += _create_textbox_requests("insight_box_" + slide_id, 60, 120, 420, 120, insight, load_theme()["body_pt"])
    requests.append({
        "createShape": {
            "objectId": "chart_box_" + slide_id,
            "shapeType": "RECTANGLE",
            "elementProperties": {
                "pageObjectId": slide_id,
                "size": {"width": {"magnitude": 520, "unit": "PT"}, "height": {"magnitude": 280, "unit": "PT"}},
                "transform": {"scaleX": 1, "scaleY": 1, "translateX": 560, "translateY": 140, "unit": "PT"},
            },
        }
    })
    requests.append({
        "insertText": {"objectId": "chart_box_" + slide_id, "text": chart_note}
    })
    requests.append({
        "updateTextStyle": {
            "objectId": "chart_box_" + slide_id,
            "style": {
                "fontFamily": load_theme()["font_family"],
                "fontSize": {"magnitude": load_theme()["body_pt"], "unit": "PT"},
                "foregroundColor": {"opaqueColor": {"rgbColor": rgb("neutral_rgb")}},
            },
            "textRange": {"type": "ALL"},
            "fields": "fontFamily,fontSize,foregroundColor",
        }
    })
    for req in requests:
        if 'createShape' in req and req['createShape']['objectId'].startswith('title_box_') or ('createShape' in req and req['createShape']['objectId'].startswith('insight_box_')):
            req['createShape']['elementProperties']['pageObjectId'] = slide_id
    service.presentations().batchUpdate(presentationId=presentation_id, body={"requests": requests}).execute()
    print(json.dumps({"presentationId": presentation_id, "createdSlideId": slide_id, "type": "title-and-chart"}, indent=2))


def duplicate_slide(presentation_id, slide_id):
    service = slides_service()
    new_slide_id = f"dup_{slide_id}"
    body = {"requests": [{"duplicateObject": {"objectId": slide_id, "objectIds": {slide_id: new_slide_id}}}]}
    service.presentations().batchUpdate(presentationId=presentation_id, body=body).execute()
    print(json.dumps({"presentationId": presentation_id, "sourceSlideId": slide_id, "newSlideId": new_slide_id}, indent=2))


def duplicate_template_slide(presentation_id, source_slide_id, new_slide_id=None):
    service = slides_service()
    target_id = new_slide_id or f"dup_{source_slide_id}"
    body = {"requests": [{"duplicateObject": {"objectId": source_slide_id, "objectIds": {source_slide_id: target_id}}}]}
    service.presentations().batchUpdate(presentationId=presentation_id, body=body).execute()
    print(json.dumps({"presentationId": presentation_id, "sourceSlideId": source_slide_id, "newSlideId": target_id}, indent=2))


def delete_slide(presentation_id, slide_id):
    service = slides_service()
    body = {"requests": [{"deleteObject": {"objectId": slide_id}}]}
    service.presentations().batchUpdate(presentationId=presentation_id, body=body).execute()
    print(json.dumps({"presentationId": presentation_id, "deletedSlideId": slide_id}, indent=2))


def show_templates():
    print(json.dumps(TEMPLATES, indent=2))


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("auth")
    sub.add_parser("show-templates")

    p_create = sub.add_parser("create-presentation")
    p_create.add_argument("--title", required=True)

    p_get = sub.add_parser("get-presentation")
    p_get.add_argument("--presentation-id", required=True)

    p_title = sub.add_parser("add-title-slide")
    p_title.add_argument("--presentation-id", required=True)
    p_title.add_argument("--title", required=True)
    p_title.add_argument("--subtitle", default="")

    p_two = sub.add_parser("create-two-column-slide")
    p_two.add_argument("--presentation-id", required=True)
    p_two.add_argument("--title", required=True)
    p_two.add_argument("--left-heading", required=True)
    p_two.add_argument("--left-bullets", nargs='+', required=True)
    p_two.add_argument("--right-heading", required=True)
    p_two.add_argument("--right-bullets", nargs='+', required=True)

    p_chart = sub.add_parser("create-title-and-chart-slide")
    p_chart.add_argument("--presentation-id", required=True)
    p_chart.add_argument("--title", required=True)
    p_chart.add_argument("--insight", required=True)
    p_chart.add_argument("--chart-note", default="Chart placeholder")

    p_theme = sub.add_parser("apply-theme")
    p_theme.add_argument("--presentation-id", required=True)

    p_font = sub.add_parser("set-font-style")
    p_font.add_argument("--font-family")
    p_font.add_argument("--title-pt", type=int)
    p_font.add_argument("--body-pt", type=int)

    p_palette = sub.add_parser("set-color-palette")
    p_palette.add_argument("--primary-rgb", nargs=3, type=int)
    p_palette.add_argument("--accent-rgb", nargs=3, type=int)
    p_palette.add_argument("--neutral-rgb", nargs=3, type=int)
    p_palette.add_argument("--background-rgb", nargs=3, type=int)

    p_dup = sub.add_parser("duplicate-slide")
    p_dup.add_argument("--presentation-id", required=True)
    p_dup.add_argument("--slide-id", required=True)

    p_del = sub.add_parser("delete-slide")
    p_del.add_argument("--presentation-id", required=True)
    p_del.add_argument("--slide-id", required=True)

    args = parser.parse_args()

    if args.cmd == "auth":
        auth()
    elif args.cmd == "show-templates":
        show_templates()
    elif args.cmd == "create-presentation":
        create_presentation(args.title)
    elif args.cmd == "get-presentation":
        get_presentation(args.presentation_id)
    elif args.cmd == "add-title-slide":
        add_title_slide(args.presentation_id, args.title, args.subtitle)
    elif args.cmd == "create-two-column-slide":
        create_two_column_slide(args.presentation_id, args.title, args.left_heading, args.left_bullets, args.right_heading, args.right_bullets)
    elif args.cmd == "create-title-and-chart-slide":
        create_title_and_chart_slide(args.presentation_id, args.title, args.insight, args.chart_note)
    elif args.cmd == "apply-theme":
        apply_theme(args.presentation_id)
    elif args.cmd == "set-font-style":
        set_font_style(args.font_family, args.title_pt, args.body_pt)
    elif args.cmd == "set-color-palette":
        set_color_palette(args.primary_rgb, args.accent_rgb, args.neutral_rgb, args.background_rgb)
    elif args.cmd == "duplicate-slide":
        duplicate_slide(args.presentation_id, args.slide_id)
    elif args.cmd == "delete-slide":
        delete_slide(args.presentation_id, args.slide_id)


if __name__ == "__main__":
    main()
