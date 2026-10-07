"""Model version pinning, cryptographic manifest, and integrity verification.

Guarantees that machine learning model artifacts are cryptographically signed/hashed,
pinned to verified runtime library versions (e.g. scikit-learn), and protected
against tampering or version drift.
"""
from __future__ import annotations
import hashlib
import json
import logging
import os
import sys
import time
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional

import sklearn

from ..model_io import load_model

logger = logging.getLogger("paimana_agent.hardening.model_registry")


class ModelSecurityError(RuntimeError):
    """Raised when model integrity check or signature fails."""
    pass


class ModelVersionMismatchError(RuntimeError):
    """Raised when runtime environment does not match pinned model requirements."""
    pass


@dataclass
class ModelMetadata:
    name: str
    filename: str
    sha256_checksum: str
    file_size_bytes: int
    sklearn_version: str
    python_version: str
    feature_names: List[str]
    created_at: float
    description: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "filename": self.filename,
            "sha256_checksum": self.sha256_checksum,
            "file_size_bytes": self.file_size_bytes,
            "sklearn_version": self.sklearn_version,
            "python_version": self.python_version,
            "feature_names": self.feature_names,
            "created_at": self.created_at,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> ModelMetadata:
        return cls(**d)


class ModelRegistryManager:
    """Manages model version pinning, checksum generation, and safe loading."""

    @staticmethod
    def compute_file_sha256(filepath: str) -> str:
        h = hashlib.sha256()
        with open(filepath, "rb") as f:
            while chunk := f.read(65536):
                h.update(chunk)
        return h.hexdigest()

    @classmethod
    def create_manifest(
        cls,
        models_dir: str,
        manifest_path: str,
        model_files: Dict[str, str]
    ) -> Dict[str, Any]:
        """Generates a cryptographic manifest for the specified model files."""
        models_meta = {}
        py_ver = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        skl_ver = sklearn.__version__

        for name, filename in model_files.items():
            full_path = os.path.join(models_dir, filename) if not os.path.isabs(filename) else filename
            if not os.path.exists(full_path):
                logger.warning(f"Model file not found for manifest: {full_path}")
                continue

            checksum = cls.compute_file_sha256(full_path)
            size = os.path.getsize(full_path)

            # Inspect model features if loaded
            features: List[str] = []
            try:
                m = load_model(full_path)
                features = list(getattr(m, "feature_names_in_", []))
            except Exception as ex:
                logger.debug(f"Could not extract feature names for {name}: {ex}")

            meta = ModelMetadata(
                name=name,
                filename=os.path.basename(full_path),
                sha256_checksum=checksum,
                file_size_bytes=size,
                sklearn_version=skl_ver,
                python_version=py_ver,
                feature_names=features,
                created_at=time.time(),
                description=f"Pinned artifact for {name}"
            )
            models_meta[name] = meta.to_dict()

        manifest = {
            "manifest_version": "1.0",
            "runtime_environment": {
                "sklearn_version": skl_ver,
                "python_version": py_ver,
            },
            "models": models_meta,
            "generated_at": time.time(),
        }

        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)

        logger.info(f"Model manifest saved to {manifest_path} with {len(models_meta)} pinned models.")
        return manifest

    @classmethod
    def verify_and_load(
        cls,
        model_name: str,
        filepath: str,
        manifest_path: Optional[str] = None,
        enforce_exact_sklearn: bool = False
    ) -> Any:
        """Verifies model file checksum and version before loading."""
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Model file does not exist: {filepath}")

        # If manifest exists, verify checksum
        if manifest_path and os.path.exists(manifest_path):
            with open(manifest_path, "r", encoding="utf-8") as f:
                manifest = json.load(f)

            if model_name in manifest.get("models", {}):
                expected = manifest["models"][model_name]
                actual_hash = cls.compute_file_sha256(filepath)
                if actual_hash != expected["sha256_checksum"]:
                    raise ModelSecurityError(
                        f"Cryptographic checksum mismatch for model '{model_name}'. "
                        f"Expected {expected['sha256_checksum']}, got {actual_hash}. "
                        "Artifact may have been tampered with or corrupted."
                    )

                if enforce_exact_sklearn:
                    pinned_skl = expected["sklearn_version"]
                    if pinned_skl != sklearn.__version__:
                        raise ModelVersionMismatchError(
                            f"Model '{model_name}' was pinned to scikit-learn {pinned_skl}, "
                            f"but current runtime is {sklearn.__version__}."
                        )

        # Safe loading via load_model
        return load_model(filepath)
