import os
import tempfile
from urllib.error import HTTPError, URLError
from urllib.request import urlopen

from fpdf import FPDF


def _safe_text(value) -> str:
    return str(value or "").encode("latin-1", "replace").decode("latin-1")


def _write_lines(pdf: FPDF, text: str, line_height: int = 8) -> None:
    for line in text.split("\n"):
        pdf.multi_cell(0, line_height, _safe_text(line))


def _download_image(url: str) -> str | None:
    if not url:
        return None

    try:
        with urlopen(url, timeout=12) as response:
            content_type = response.headers.get("Content-Type", "")
            suffix = ".jpg"
            if "png" in content_type:
                suffix = ".png"
            image_bytes = response.read()
    except (HTTPError, URLError, TimeoutError):
        return None

    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    temp_file.write(image_bytes)
    temp_file.close()
    return temp_file.name


def _add_image(pdf: FPDF, image_path: str, width: int = 90) -> None:
    if pdf.get_y() > 230:
        pdf.add_page()
    pdf.image(image_path, w=width)
    pdf.ln(4)


def _add_route_links(pdf: FPDF, route_paths: list[dict]) -> None:
    if not route_paths:
        return

    pdf.add_page()
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "Daily Route Links", ln=True)
    pdf.set_font("Arial", size=10)

    for route in route_paths:
        distance_km = route.get("distance_meters", 0) / 1000
        duration_min = route.get("duration_seconds", 0) // 60
        label = f"Day {route.get('day')}: {distance_km:.1f} km, about {duration_min} min"
        maps_url = route.get("maps_url", "")
        _write_lines(pdf, f"{label}\n{maps_url}\n")


def _add_place_links(pdf: FPDF, map_points: list[dict]) -> None:
    if not map_points:
        return

    pdf.add_page()
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "Map Places", ln=True)
    pdf.set_font("Arial", size=10)

    for point in map_points:
        label = f"Day {point.get('day')}" if point.get("day") else "Hotel"
        name = point.get("name", "")
        maps_url = point.get("maps_url", "")
        _write_lines(pdf, f"{label}: {name}\n{maps_url}\n")


def _add_place_images(pdf: FPDF, map_points: list[dict], max_images: int = 8) -> None:
    image_points = [
        point
        for point in map_points
        if point.get("photo_url") and point.get("type") in {"attraction", "restaurant", "activity"}
    ][:max_images]
    if not image_points:
        return

    temp_images = []
    pdf.add_page()
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "Place Photos", ln=True)
    pdf.set_font("Arial", size=10)
    _write_lines(pdf, "Images are provided by Google Places where available.\n")

    try:
        for point in image_points:
            image_path = _download_image(point.get("photo_url", ""))
            if not image_path:
                continue

            temp_images.append(image_path)
            pdf.set_font("Arial", "B", 11)
            _write_lines(pdf, point.get("name", "Place"))
            _add_image(pdf, image_path)
    finally:
        for image_path in temp_images:
            try:
                os.remove(image_path)
            except OSError:
                pass


def export_to_pdf(itinerary_text, map_points=None, route_paths=None):
    map_points = map_points or []
    route_paths = route_paths or []
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    try:
        _write_lines(pdf, itinerary_text, line_height=9)
        _add_route_links(pdf, route_paths)
        _add_place_links(pdf, map_points)
        _add_place_images(pdf, map_points)

        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
        pdf.output(temp_file.name)
        return temp_file.name
    except Exception as e:
        raise Exception(f"PDF generation failed: {str(e)}")
