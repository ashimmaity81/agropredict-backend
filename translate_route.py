# translate_route.py
# Place this file in your backend folder (same folder as main.py)
#
# Install dependency once:
#     pip install deep-translator
#
# This file is already imported in main.py — no other changes needed.

from fastapi import APIRouter
from pydantic import BaseModel
from typing import List

router = APIRouter()

SUPPORTED_TARGETS = {"hi", "bn", "pa"}

class TranslateRequest(BaseModel):
    texts: List[str]
    target: str        # "hi" | "bn" | "pa"

class TranslateResponse(BaseModel):
    translations: List[str]


@router.post("/translate", response_model=TranslateResponse)
def translate_texts(req: TranslateRequest):
    """
    Translate a batch of English strings to the requested language.
    Falls back to original text on any error — never crashes the app.
    """
    # Return originals for English or unsupported language codes
    if req.target == "en" or req.target not in SUPPORTED_TARGETS:
        return TranslateResponse(translations=req.texts)

    try:
        from deep_translator import GoogleTranslator
        translator = GoogleTranslator(source="en", target=req.target)
    except ImportError:
        # deep-translator not installed — silently return originals
        return TranslateResponse(translations=req.texts)

    results: List[str] = []

    for text in req.texts:
        try:
            if not text or not text.strip():
                results.append(text)
            else:
                translated = translator.translate(text.strip())
                results.append(translated if translated else text)
        except Exception as e:
            print("Translation Error:", str(e))
            results.append(text)   # always fall back, never crash

    return TranslateResponse(translations=results)