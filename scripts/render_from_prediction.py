import json
from pathlib import Path

from scripts.render_schematic import render_sample_image


def prediction_to_sample(prediction, prompt, sample_id="notebook_sample", source_template_id="notebook_inference"):
    return {
        "id": sample_id,
        "source_template_id": source_template_id,
        "prompt": prompt,
        "output": prediction,
    }


def render_prediction_image(prediction, prompt, sample_id="notebook_sample", source_template_id="notebook_inference"):
    sample = prediction_to_sample(
        prediction=prediction,
        prompt=prompt,
        sample_id=sample_id,
        source_template_id=source_template_id,
    )
    return render_sample_image(sample)


def render_prediction_file(prediction, prompt, output_path, sample_id="notebook_sample", source_template_id="notebook_inference"):
    image = render_prediction_image(
        prediction=prediction,
        prompt=prompt,
        sample_id=sample_id,
        source_template_id=source_template_id,
    )
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(output_path)
    return output_path


def save_prediction_json(prediction, output_path):
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(prediction, ensure_ascii=False, indent=2), encoding="utf-8")
    return output_path
