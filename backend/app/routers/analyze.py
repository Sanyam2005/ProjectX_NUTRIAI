import io
import logging

from fastapi import APIRouter, File, Form, UploadFile

from app.ai import get_meal_analyzer
from app.deps import CurrentUser
from app.schemas.meal import AnalyzeMealResponse, IngredientIn, NutritionTotals
from app.services.storage import get_storage

log = logging.getLogger(__name__)

# Register HEIC opener once at import time so PIL can read iPhone photos.
# pillow-heif is a soft dependency: if it's not installed, HEIC uploads simply
# fall through and the AI provider will reject the unknown content-type.
try:
    from pillow_heif import register_heif_opener  # type: ignore

    register_heif_opener()
    _HEIC_OK = True
except Exception:  # pragma: no cover
    _HEIC_OK = False

router = APIRouter(prefix="/api", tags=["analyze"])


def _is_heic(content: bytes, content_type: str | None, filename: str | None) -> bool:
    ct = (content_type or "").lower()
    if "heic" in ct or "heif" in ct:
        return True
    if filename and filename.lower().rsplit(".", 1)[-1] in ("heic", "heif"):
        return True
    # ISO BMFF "ftyp" box at offset 4 with a HEIC brand.
    head = content[:32]
    if len(head) >= 12 and head[4:8] == b"ftyp":
        brand = head[8:12]
        if brand in (b"heic", b"heix", b"hevc", b"hevx", b"mif1", b"msf1"):
            return True
    return False


def _transcode_heic_to_jpeg(content: bytes) -> bytes:
    from PIL import Image  # local import keeps boot fast

    with Image.open(io.BytesIO(content)) as im:
        buf = io.BytesIO()
        im.convert("RGB").save(buf, "JPEG", quality=88, optimize=True)
        return buf.getvalue()


@router.post("/analyze-meal", response_model=AnalyzeMealResponse)
async def analyze_meal(
    _: CurrentUser,
    image: UploadFile = File(...),
    save_image: bool = Form(True),
) -> AnalyzeMealResponse:
    """Run the AI pipeline on an uploaded meal image and return editable results."""
    content = await image.read()
    content_type = image.content_type or "image/jpeg"
    filename = image.filename

    if _HEIC_OK and _is_heic(content, content_type, filename):
        try:
            content = _transcode_heic_to_jpeg(content)
            content_type = "image/jpeg"
            if filename:
                filename = filename.rsplit(".", 1)[0] + ".jpg"
        except Exception as exc:
            log.warning("HEIC transcode failed for %r: %s", filename, exc)

    image_url: str | None = None
    if save_image:
        try:
            image_url = await get_storage().save(
                content,
                content_type=content_type,
                filename=filename,
            )
        except Exception:
            image_url = None  # storage is best-effort

    analyzer = get_meal_analyzer()
    analysis = await analyzer.analyze(content, filename=filename)

    ingredients = [
        IngredientIn(
            name=i.name,
            weight_g=i.weight_g,
            unit=i.unit,
            confidence=i.confidence,
            calories=i.calories,
            protein_g=i.protein_g,
            carbs_g=i.carbs_g,
            fat_g=i.fat_g,
            fiber_g=i.fiber_g,
            sugar_g=i.sugar_g,
            sodium_mg=i.sodium_mg,
        )
        for i in analysis.ingredients
    ]
    totals = NutritionTotals(**analysis.totals)

    return AnalyzeMealResponse(
        meal_name=analysis.meal_name,
        meal_type=analysis.meal_type,
        image_url=image_url,
        confidence=analysis.confidence,
        engine=getattr(analyzer, "engine_label", "AI"),
        ingredients=ingredients,
        totals=totals,
    )
