from __future__ import annotations

import argparse
import json
from pathlib import Path

from janggi import LinearValueTrainer, TrainingDataset


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Train a dependency-free Janggi linear value model."
    )
    parser.add_argument(
        "--dataset",
        type=Path,
        required=True,
        help="Path to a janggi-training-v1 JSON dataset.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("linear-value-model.json"),
        help="Output path for the trained model.",
    )
    parser.add_argument(
        "--ridge",
        type=float,
        default=1.0,
        help="Ridge regularization strength.",
    )
    parser.add_argument(
        "--target-scale-cp",
        type=float,
        default=3000.0,
        help="Absolute centipawn-like target assigned to WIN/LOSS examples.",
    )
    args = parser.parse_args()

    dataset_text = args.dataset.read_text(encoding="utf-8")
    dataset = TrainingDataset.from_json(dataset_text)
    trainer = LinearValueTrainer(
        ridge=args.ridge,
        target_scale_cp=args.target_scale_cp,
    )
    model = trainer.fit(dataset)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        model.to_json() + "\n",
        encoding="utf-8",
    )

    summary = {
        "dataset_format": "janggi-training-v1",
        "training_examples": len(dataset),
        "model_format": "janggi-linear-value-v1",
        "feature_count": len(model.weights),
        "ridge": trainer.ridge,
        "target_scale_cp": trainer.target_scale_cp,
        "output": str(args.output),
    }
    print("Linear value model trained")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
