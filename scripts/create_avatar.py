#!/usr/bin/env python3
"""
D&D Character Avatar Generator

Generates a character portrait using Stable Diffusion (SDXL-Turbo).
Loads an existing character JSON, then either:
  - Auto-generates a portrait from character stats
  - Guides you through a customization Q&A to build the prompt

Usage:
    python create_avatar.py
    python create_avatar.py --character characters/zyk.json
"""

import argparse
import json
import os
import sys
from pathlib import Path

# ── Dependency check ────────────────────────────────────────────────────────

def check_dependencies():
    missing = []
    try:
        import torch
        if not torch.cuda.is_available():
            print("WARNING: CUDA not available — generation will be very slow on CPU.")
    except ImportError:
        missing.append("torch  (install: pip install torch --index-url https://download.pytorch.org/whl/cu124)")
    try:
        import diffusers  # noqa: F401
    except ImportError:
        missing.append("diffusers  (install: pip install diffusers accelerate)")
    try:
        import accelerate  # noqa: F401
    except ImportError:
        missing.append("accelerate  (install: pip install accelerate)")

    if missing:
        print("\nMissing dependencies:")
        for m in missing:
            print(f"  - {m}")
        sys.exit(1)

check_dependencies()

import torch
from diffusers import AutoPipelineForText2Image

# ── Constants ────────────────────────────────────────────────────────────────

MODEL_ID = "stabilityai/sdxl-turbo"
PORTRAITS_DIR = Path(__file__).parent / "characters" / "portraits"

# D&D race → visual descriptors for SD prompt
RACE_KEYWORDS = {
    "Dragonborn":  "dragonborn, reptilian humanoid, scaled skin, draconic features, horn-like ridges",
    "Dwarf":       "dwarf, stocky build, thick beard, sturdy",
    "Elf":         "elf, slender, pointed ears, ethereal features",
    "Gnome":       "gnome, small stature, large curious eyes, whimsical",
    "Half-Elf":    "half-elf, slightly pointed ears, mixed human and elven features",
    "Halfling":    "halfling, short stature, curly hair, rosy cheeks",
    "Half-Orc":    "half-orc, grey-green skin, prominent tusks, muscular",
    "Human":       "human adventurer, determined expression",
    "Tiefling":    "tiefling, small curved horns, solid-colored eyes, long tail, infernal heritage",
}

# D&D class → visual descriptors
CLASS_KEYWORDS = {
    "Barbarian": "fur-trimmed armor, battle scars, wild eyes, great axe",
    "Bard":      "colorful traveling clothes, lute, charming smile, feathered cap",
    "Cleric":    "holy symbol, chainmail, divine radiance, robes",
    "Druid":     "leather armor, wooden staff, vines and leaves, nature magic",
    "Fighter":   "plate armor, sword and shield, battle-hardened, scars",
    "Monk":      "simple robes, bare feet, calm focused expression, prayer beads",
    "Paladin":   "shining plate armor, holy sword, divine aura, cape",
    "Ranger":    "forest cloak, longbow, hunting leathers, quiver",
    "Rogue":     "dark hood, daggers, shadow, leather armor, sly expression",
    "Sorcerer":  "elegant robes, magical energy, arcane runes, flowing hair",
    "Warlock":   "dark robes, eldritch glow, mysterious, pact focus",
    "Wizard":    "arcane robes, spellbook, staff, spectacles, magical aura",
}

# Alignment → mood/expression descriptors
ALIGNMENT_KEYWORDS = {
    "Lawful Good":     "noble and righteous expression, calm, trustworthy",
    "Neutral Good":    "kind eyes, gentle expression, compassionate",
    "Chaotic Good":    "rebellious smile, adventurous look, free-spirited",
    "Lawful Neutral":  "stern and disciplined, stoic, professional",
    "True Neutral":    "balanced, thoughtful, observant",
    "Chaotic Neutral": "unpredictable smirk, wild eyes, eccentric",
    "Lawful Evil":     "cold calculating gaze, menacing, authoritative",
    "Neutral Evil":    "cruel expression, self-serving, dangerous",
    "Chaotic Evil":    "unhinged grin, volatile, destructive energy",
}

# Background → setting/context hints
BACKGROUND_KEYWORDS = {
    "Acolyte":      "religious setting, temple background",
    "Charlatan":    "urban setting, merchant district",
    "Criminal":     "dark alley, shadows",
    "Entertainer":  "tavern stage, colorful backdrop",
    "Folk Hero":    "rural village, humble origins",
    "Guild Artisan":"workshop, crafting tools",
    "Hermit":       "forest retreat, solitude",
    "Noble":        "castle interior, rich tapestry background",
    "Outlander":    "wilderness, mountains, open sky",
    "Sage":         "library, scrolls, candlelight",
    "Sailor":       "ship deck, ocean horizon",
    "Soldier":      "battlefield, military camp",
    "Urchin":       "city streets, worn clothing",
}

STYLE_SUFFIX = (
    "fantasy portrait, D&D 5e art style, highly detailed, dramatic lighting, "
    "digital painting, concept art, artstation trending, 8k"
)

NEGATIVE_PROMPT = (
    "blurry, low quality, deformed, extra limbs, bad anatomy, "
    "watermark, text, signature, ugly, bad proportions"
)


# ── Helpers ──────────────────────────────────────────────────────────────────

def find_character_files() -> list[Path]:
    root = Path(__file__).parent.parent / "characters"
    files = sorted(root.glob("**/*.json"))
    # Filter to files that look like characters (have 'name' and 'race' keys)
    result = []
    for f in files:
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            if "name" in data and "race" in data:
                result.append(f)
        except Exception:
            pass
    return result


def load_character(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def save_character(path: Path, data: dict):
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def ask(prompt: str, default: str = "") -> str:
    hint = f" [{default}]" if default else ""
    raw = input(f"{prompt}{hint}: ").strip()
    return raw if raw else default


def choose(prompt: str, options: list[str], default_idx: int = 0) -> str:
    print(f"\n{prompt}")
    for i, opt in enumerate(options, 1):
        marker = " (default)" if i - 1 == default_idx else ""
        print(f"  {i}. {opt}{marker}")
    while True:
        raw = input(f"Select (1-{len(options)}): ").strip()
        if not raw:
            return options[default_idx]
        if raw.isdigit() and 1 <= int(raw) <= len(options):
            return options[int(raw) - 1]
        print("  Invalid choice, try again.")


# ── Prompt builders ──────────────────────────────────────────────────────────

def build_auto_prompt(char: dict) -> tuple[str, str]:
    """Build prompt automatically from character JSON fields."""
    parts = []

    race = char.get("race", "human")
    cls  = char.get("character_class", "adventurer")
    aln  = char.get("alignment", "")
    bg   = char.get("background", "")

    # Subject line
    parts.append(f"portrait of a {race} {cls}")

    # Race visual traits
    race_kw = RACE_KEYWORDS.get(race, f"{race.lower()} fantasy character")
    parts.append(race_kw)

    # Class visual traits
    class_kw = CLASS_KEYWORDS.get(cls, f"{cls.lower()} adventurer equipment")
    parts.append(class_kw)

    # Alignment mood
    if aln in ALIGNMENT_KEYWORDS:
        parts.append(ALIGNMENT_KEYWORDS[aln])

    # Background setting
    if bg in BACKGROUND_KEYWORDS:
        parts.append(BACKGROUND_KEYWORDS[bg])

    prompt = ", ".join(parts) + ", " + STYLE_SUFFIX
    return prompt, NEGATIVE_PROMPT


def build_custom_prompt(char: dict) -> tuple[str, str]:
    """Build prompt via interactive Q&A, fixing race/class from character."""
    race = char.get("race", "human")
    cls  = char.get("character_class", "adventurer")
    aln  = char.get("alignment", "")
    bg   = char.get("background", "")

    print(f"\n  Race:  {race}  (fixed)")
    print(f"  Class: {cls}  (fixed)")
    if aln:
        print(f"  Alignment: {aln}  (fixed)")
    if bg:
        print(f"  Background: {bg}  (fixed)")

    print("\nAnswer the questions below. Press Enter to skip / use the default.\n")

    # Gender presentation
    gender = choose(
        "Gender presentation:",
        ["male", "female", "androgynous", "non-binary"],
        default_idx=0,
    )

    # Age feel
    age = choose(
        "Age feel:",
        ["young (teens-20s)", "adult (30s-40s)", "middle-aged (50s)", "elder (60s+)"],
        default_idx=1,
    )

    # Hair
    hair_color = ask("Hair color", "dark brown")
    hair_style = ask("Hair style (e.g. long wavy, short braided, shaved)", "medium length")

    # Eyes
    eye_color = ask("Eye color", "brown")

    # Skin / complexion
    skin = ask("Skin tone / complexion (e.g. pale, tanned, dark, scaled green)", "")

    # Mood / expression
    mood = ask("Expression / mood (e.g. fierce, serene, smirking, battle-worn)", "determined")

    # Clothing
    clothes = ask(
        "Clothing details (e.g. torn battle robes, ornate noble armor, simple leather)",
        "",
    )

    # Environment / background
    environment = ask(
        "Environment / background (e.g. misty forest, torch-lit dungeon, castle throne room)",
        "dramatic fantasy backdrop",
    )

    # Art vibe
    vibe = choose(
        "Art style vibe:",
        [
            "realistic painterly (dark fantasy)",
            "bright heroic (classic D&D art)",
            "anime / manga inspired",
            "gritty grimdark",
            "watercolor storybook",
        ],
        default_idx=1,
    )

    # Extra freeform
    extra = ask("Anything else to add? (optional)", "")

    # ── Assemble prompt ──────────────────────────────────────────────────────
    parts = [f"{gender} {race} {cls}"]
    parts.append(RACE_KEYWORDS.get(race, race.lower()))
    parts.append(CLASS_KEYWORDS.get(cls, cls.lower()))

    if aln in ALIGNMENT_KEYWORDS:
        parts.append(ALIGNMENT_KEYWORDS[aln])
    if bg in BACKGROUND_KEYWORDS:
        parts.append(BACKGROUND_KEYWORDS[bg])

    parts.append(f"{age.split('(')[0].strip()} appearance")
    parts.append(f"{hair_color} {hair_style} hair")
    parts.append(f"{eye_color} eyes")
    if skin:
        parts.append(f"{skin} skin")
    parts.append(f"{mood} expression")
    if clothes:
        parts.append(clothes)
    parts.append(environment)
    if extra:
        parts.append(extra)

    # Vibe maps to style suffix override
    vibe_styles = {
        "realistic painterly (dark fantasy)": "dark fantasy portrait, oil painting style, dramatic shadows, highly detailed",
        "bright heroic (classic D&D art)":    "heroic fantasy portrait, D&D 5e art style, bright colors, digital painting, artstation",
        "anime / manga inspired":             "anime fantasy portrait, manga style, cel shaded, detailed linework",
        "gritty grimdark":                    "grimdark fantasy, gritty, dark atmosphere, battle-worn, realistic",
        "watercolor storybook":               "watercolor painting, storybook illustration, soft colors, whimsical fantasy",
    }
    style = vibe_styles.get(vibe, STYLE_SUFFIX)
    parts.append(style)

    prompt = ", ".join(p for p in parts if p)
    return prompt, NEGATIVE_PROMPT


# ── SD pipeline ──────────────────────────────────────────────────────────────

def load_pipeline():
    print(f"\nLoading {MODEL_ID}...")
    print("(First run downloads ~6GB — subsequent runs load from cache)\n")

    pipe = AutoPipelineForText2Image.from_pretrained(
        MODEL_ID,
        torch_dtype=torch.float16,
        variant="fp16",
    )
    pipe = pipe.to("cuda")
    pipe.enable_attention_slicing()  # reduce VRAM usage
    return pipe


def generate_image(pipe, prompt: str, negative_prompt: str, steps: int = 4) -> "PIL.Image.Image":
    print(f"\nGenerating portrait ({steps} steps)...")
    print(f"Prompt: {prompt[:120]}{'...' if len(prompt) > 120 else ''}\n")

    # SDXL-Turbo uses guidance_scale=0.0 and needs few steps
    result = pipe(
        prompt=prompt,
        negative_prompt=negative_prompt,
        num_inference_steps=steps,
        guidance_scale=0.0,
        width=512,
        height=512,
    )
    return result.images[0]


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Generate a D&D character portrait with Stable Diffusion")
    parser.add_argument("--character", "-c", help="Path to character JSON file")
    parser.add_argument("--steps", type=int, default=4, help="SD inference steps (default: 4)")
    parser.add_argument("--output", "-o", help="Output image path (default: characters/portraits/<name>.png)")
    args = parser.parse_args()

    print("\n" + "=" * 60)
    print("  D&D CHARACTER AVATAR GENERATOR")
    print("  Powered by SDXL-Turbo (Stable Diffusion)")
    print("=" * 60)

    # ── Select character ─────────────────────────────────────────────────────
    char_path: Path

    if args.character:
        char_path = Path(args.character)
        if not char_path.exists():
            print(f"Error: file not found: {char_path}")
            sys.exit(1)
    else:
        files = find_character_files()
        if not files:
            print("No character JSON files found in project directory.")
            sys.exit(1)

        print("\nAvailable characters:")
        for i, f in enumerate(files, 1):
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
                label = f"  {i}. {data.get('name', '?')} — {data.get('race', '?')} {data.get('character_class', '?')}  ({f})"
            except Exception:
                label = f"  {i}. {f}"
            print(label)

        while True:
            raw = input(f"\nSelect character (1-{len(files)}): ").strip()
            if raw.isdigit() and 1 <= int(raw) <= len(files):
                char_path = files[int(raw) - 1]
                break
            print("  Invalid choice.")

    char = load_character(char_path)
    print(f"\nLoaded: {char.get('name')} — {char.get('race')} {char.get('character_class')}")

    # ── Generation mode ──────────────────────────────────────────────────────
    mode = choose(
        "How would you like to generate the portrait?",
        [
            "Auto-generate from character stats",
            "Customize (interactive Q&A)",
        ],
    )

    if "Auto" in mode:
        prompt, negative_prompt = build_auto_prompt(char)
    else:
        prompt, negative_prompt = build_custom_prompt(char)

    print(f"\nFinal prompt:\n  {prompt}")
    print(f"\nNegative prompt:\n  {negative_prompt}")

    confirm = input("\nProceed with generation? (y/n) [y]: ").strip().lower()
    if confirm == "n":
        print("Aborted.")
        sys.exit(0)

    # ── Output path ──────────────────────────────────────────────────────────
    if args.output:
        output_path = Path(args.output)
    else:
        PORTRAITS_DIR.mkdir(parents=True, exist_ok=True)
        safe_name = char.get("name", "character").replace(" ", "_").lower()
        output_path = PORTRAITS_DIR / f"{safe_name}.png"

    # ── Generate ─────────────────────────────────────────────────────────────
    pipe = load_pipeline()
    image = generate_image(pipe, prompt, negative_prompt, steps=args.steps)

    image.save(output_path)
    print(f"\nPortrait saved to: {output_path}")

    # ── Update character JSON ─────────────────────────────────────────────────
    char["image_path"] = str(output_path)
    save_character(char_path, char)
    print(f"Updated {char_path.name} with image_path.")

    print("\nDone! Load the character in the web UI to see the portrait.")
    print("=" * 60)


if __name__ == "__main__":
    main()
