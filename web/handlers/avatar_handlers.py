"""
Avatar generation handler for the Gradio web UI.

Wraps the SD generation logic from scripts/create_avatar.py so it can be
called from Gradio event handlers without any interactive CLI prompts.
"""

import sys
import json
from pathlib import Path
from typing import Optional, Tuple

# Ensure project root is on path
_PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(_PROJECT_ROOT))

# Re-use prompt-building helpers and constants from the CLI script
sys.path.insert(0, str(_PROJECT_ROOT / "scripts"))
from create_avatar import (
    RACE_KEYWORDS,
    CLASS_KEYWORDS,
    ALIGNMENT_KEYWORDS,
    BACKGROUND_KEYWORDS,
    STYLE_SUFFIX,
    NEGATIVE_PROMPT,
    PORTRAITS_DIR,
    clip_trim,
)

_CHARACTERS_DIR = _PROJECT_ROOT / "characters"

# Lazy-loaded pipeline — loaded on first generation, then cached
_pipe = None


def _get_pipeline():
    global _pipe
    if _pipe is None:
        try:
            import torch
            from diffusers import AutoPipelineForText2Image
        except ImportError:
            raise RuntimeError(
                "diffusers / torch not installed. "
                "Run: pip install diffusers accelerate torch --index-url https://download.pytorch.org/whl/cu124"
            )
        if not torch.cuda.is_available():
            raise RuntimeError("CUDA GPU not available. Portrait generation requires a GPU.")

        from create_avatar import MODEL_ID
        _pipe = AutoPipelineForText2Image.from_pretrained(
            MODEL_ID,
            torch_dtype=torch.float16,
            variant="fp16",
        )
        _pipe = _pipe.to("cuda")
        _pipe.enable_attention_slicing()
    return _pipe


def _build_auto_prompt(race: str, char_class: str, alignment: str, background: str) -> str:
    parts = [f"portrait of a {race} {char_class}"]
    parts.append(RACE_KEYWORDS.get(race, f"{race.lower()} fantasy character"))
    parts.append(CLASS_KEYWORDS.get(char_class, f"{char_class.lower()} adventurer"))
    if alignment in ALIGNMENT_KEYWORDS:
        parts.append(ALIGNMENT_KEYWORDS[alignment])
    if background in BACKGROUND_KEYWORDS:
        parts.append(BACKGROUND_KEYWORDS[background])
    parts.append(STYLE_SUFFIX)
    return ", ".join(parts)


def _build_custom_prompt(
    race: str, char_class: str, alignment: str, background: str,
    gender: str,
    hair: str, eyes: str, skin: str, mood: str,
    clothes: str, environment: str, art_style: str, extra: str,
) -> str:
    vibe_styles = {
        "bright heroic (classic D&D art)":    "D&D fantasy portrait, bright colors, digital painting",
        "realistic painterly (dark fantasy)": "dark fantasy portrait, oil painting, dramatic shadows",
        "anime / manga inspired":             "anime fantasy portrait, manga style, cel shaded",
        "gritty grimdark":                    "grimdark fantasy portrait, gritty, battle-worn",
        "watercolor storybook":               "watercolor fantasy portrait, soft colors, storybook",
    }

    # User's explicit choices come first so clip_trim keeps them over generic keywords
    parts = [f"{gender} {race} {char_class} fantasy portrait"]
    if hair:
        parts.append(f"{hair} hair")
    if eyes:
        parts.append(f"{eyes} eyes")
    if skin:
        parts.append(f"{skin} skin")
    if mood:
        parts.append(f"{mood} expression")
    if clothes:
        parts.append(clothes)
    if environment:
        parts.append(environment)
    if extra:
        parts.append(extra)
    # Generic keyword expansions are lower priority — trimmed first if over limit
    if alignment in ALIGNMENT_KEYWORDS:
        parts.append(ALIGNMENT_KEYWORDS[alignment])
    parts.append(vibe_styles.get(art_style, "fantasy portrait, digital painting"))
    return ", ".join(p for p in parts if p)


def _load_char_from_selector(char_selector: str) -> Optional[dict]:
    """Load character data dict from a dropdown selection string like 'Name (Race Class)'."""
    if not char_selector or char_selector.startswith("—"):
        return None
    name = char_selector.split("(")[0].strip()
    filepath = _CHARACTERS_DIR / f"{name.lower().replace(' ', '_')}.json"
    if filepath.exists():
        return json.loads(filepath.read_text(encoding="utf-8"))
    return None


def generate_avatar(
    # Saved-character selector (overrides form fields when set)
    char_selector: str,
    # Character identity (from create-tab form fields)
    name: str,
    race: str,
    char_class: str,
    alignment: str,
    background: str,
    # Mode
    mode: str,
    # Always-visible field
    gender: str,
    hair: str,
    eyes: str,
    skin: str,
    mood: str,
    clothes: str,
    environment: str,
    art_style: str,
    extra: str,
) -> Tuple[Optional[str], str]:
    """
    Generate a character portrait and return (image_path, status_message).

    Called by the Gradio "Generate Portrait" button in the Create Character tab.
    """
    char_data = _load_char_from_selector(char_selector)
    if char_data:
        name = char_data.get("name", name or "character")
        race = char_data.get("race", race or "Human")
        char_class = char_data.get("character_class", char_class or "Fighter")
        alignment = char_data.get("alignment", alignment or "")
        background = char_data.get("background", background or "")

    name = (name or "character").strip()
    race = (race or "Human").strip()
    char_class = (char_class or "Fighter").strip()

    try:
        # Build prompt
        if "Auto" in mode:
            prompt = _build_auto_prompt(race, char_class, alignment or "", background or "")
        else:
            prompt = _build_custom_prompt(
                race, char_class, alignment or "", background or "",
                gender or "female",
                hair or "", eyes or "", skin or "", mood or "determined",
                clothes or "", environment or "dramatic fantasy backdrop",
                art_style or "bright heroic (classic D&D art)", extra or "",
            )

        # Load pipeline (lazy, cached)
        status_loading = "Loading Stable Diffusion pipeline..."
        pipe = _get_pipeline()

        # Trim to CLIP limit
        prompt = clip_trim(pipe, prompt)
        neg    = clip_trim(pipe, NEGATIVE_PROMPT)

        # Generate
        import torch
        result = pipe(
            prompt=prompt,
            negative_prompt=neg,
            num_inference_steps=4,
            guidance_scale=0.0,
            width=512,
            height=512,
        )
        image = result.images[0]

        # Save
        PORTRAITS_DIR.mkdir(parents=True, exist_ok=True)
        safe_name = name.replace(" ", "_").lower()
        output_path = PORTRAITS_DIR / f"{safe_name}.png"
        image.save(output_path)

        # Update character JSON if it exists
        char_json = _PROJECT_ROOT / "characters" / f"{safe_name}.json"
        if not char_json.exists():
            # also try project root
            char_json = _PROJECT_ROOT / f"{safe_name}.json"
        if char_json.exists():
            data = json.loads(char_json.read_text(encoding="utf-8"))
            data["image_path"] = str(output_path)
            char_json.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
            saved_note = f" | {char_json.name} updated"
        else:
            saved_note = " | Save character to link portrait to JSON"

        status = f"Portrait saved to {output_path}{saved_note}"
        return str(output_path), status

    except RuntimeError as e:
        return None, f"Error: {e}"
    except Exception as e:
        return None, f"Unexpected error: {e}"


def toggle_custom_fields(mode: str):
    """Show/hide custom fields based on mode radio selection."""
    import gradio as gr
    return gr.update(visible="Custom" in mode)
