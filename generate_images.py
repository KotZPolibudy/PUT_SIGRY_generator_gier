import argparse
import json
import os
from pathlib import Path
import torch
from diffusers import StableDiffusionPipeline

MODEL_ID = "runwayml/stable-diffusion-v1-5"


def build_scene_prompt(quest_data):
    locations = quest_data.get("locations", {})
    items = quest_data.get("items", {})
    characters = quest_data.get("characters", {})

    def short(text):
        """
        Max 77 token can be used for the prompt, but we want to be concise and focus on key details.
        Heuristic shortening - we don't count tokens perfectly,
        but control length and priority of information.
        """
        text = text.strip()

        # remove very long sentences
        sentences = text.split(".")
        sentences = [s.strip() for s in sentences if s.strip()]

        # take only the first 2 sentences for brevity
        return ". ".join(sentences[:2])

    def pack(data, limit):
        """
        Selects the most important elements based on description length and applies shortening.:
        - characters first
        - then locations
        - then items
        """
        values = list(data.values())

        # sort by description length (assuming longer descriptions are more detailed)
        values = sorted(values, key=lambda x: len(x.get("description", "")))

        out = []
        for v in values[:limit]:
            out.append(short(v.get("description", "")))

        return "\n".join(out)

    character_text = pack(characters, limit=2)  # max 2 characters for short prompt
    location_text = pack(locations, limit=2)
    item_text = pack(items, limit=2)

    prompt = f"""
Fantasy RPG scene.

Characters:
{character_text}

Location:
{location_text}

Objects:
{item_text}

cinematic fantasy illustration, game concept art
""".strip()

    return prompt


def load_pipeline():
    device = "cuda" if torch.cuda.is_available() else "cpu"
    pipe = StableDiffusionPipeline.from_pretrained(
        MODEL_ID, torch_dtype=torch.float16 if device == "cuda" else torch.float32
    )
    pipe = pipe.to(device)
    if device == "cuda":
        pipe.enable_attention_slicing()
        pipe.vae.enable_slicing()
    return pipe


def generate_image(pipe, prompt, output_path):
    image = pipe(prompt, num_inference_steps=30, guidance_scale=7.5).images[0]
    image.save(output_path)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--story_name", required=True, help="Folder inside quests/")

    args = parser.parse_args()

    story_dir = Path("quests") / args.story_name
    if not story_dir.exists():
        raise FileNotFoundError(f"Story directory not found: {story_dir}")

    image_dir = story_dir / "images"
    image_dir.mkdir(exist_ok=True)
    quest_files = sorted(story_dir.glob("quest_*.json"))

    if not quest_files:
        raise RuntimeError(f"No quest JSON files found in {story_dir}")

    print("Loading diffusion model...")
    pipe = load_pipeline()

    for quest_file in quest_files:
        print(f"Processing {quest_file.name}")

        with open(quest_file, "r", encoding="utf-8") as f:
            quest_data = json.load(f)

        prompt = build_scene_prompt(quest_data)
        quest_number = quest_file.stem.split("_")[1]
        output_path = image_dir / f"quest_{quest_number}.png"
        print(f"Generating image -> {output_path}")
        generate_image(pipe, prompt, output_path)

    print("Done.")


if __name__ == "__main__":
    main()
