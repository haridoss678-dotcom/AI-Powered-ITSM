from __future__ import annotations

import ctypes
import importlib.util
import os
import shutil
import sys
import threading
import time
from pathlib import Path
from typing import Any

from app.core.config import get_settings
from app.core.errors import AppError, ErrorCode

MIN_AVAILABLE_MEMORY_BYTES = 1 * 1024**3
MAX_INPUT_TOKENS = 2048
MAX_GENERATION_TOKENS = 256


def _available_memory_bytes() -> int:
    if sys.platform == "win32":
        class MemoryStatus(ctypes.Structure):
            _fields_ = [
                ("dwLength", ctypes.c_ulong),
                ("dwMemoryLoad", ctypes.c_ulong),
                ("ullTotalPhys", ctypes.c_ulonglong),
                ("ullAvailPhys", ctypes.c_ulonglong),
                ("ullTotalPageFile", ctypes.c_ulonglong),
                ("ullAvailPageFile", ctypes.c_ulonglong),
                ("ullTotalVirtual", ctypes.c_ulonglong),
                ("ullAvailVirtual", ctypes.c_ulonglong),
                ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
            ]

        memory_status = MemoryStatus()
        memory_status.dwLength = ctypes.sizeof(MemoryStatus)
        if not ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(memory_status)):
            raise OSError("Unable to read available system memory.")
        return int(memory_status.ullAvailPhys)

    try:
        return int(os.sysconf("SC_AVPHYS_PAGES") * os.sysconf("SC_PAGE_SIZE"))
    except (AttributeError, OSError, ValueError) as exc:
        raise OSError("Unable to read available system memory.") from exc


def _model_snapshot_dirs(model_id: str) -> list[Path]:
    cache_root = Path(
        os.environ.get("HUGGINGFACE_HUB_CACHE")
        or (Path(os.environ.get("HF_HOME", Path.home() / ".cache" / "huggingface")) / "hub")
    )
    model_cache = cache_root / f"models--{model_id.replace('/', '--')}" / "snapshots"
    if not model_cache.is_dir():
        return []
    return [path for path in model_cache.iterdir() if path.is_dir()]


def _is_model_fully_cached(model_id: str) -> bool:
    for snapshot in _model_snapshot_dirs(model_id):
        has_config = (snapshot / "config.json").is_file()
        has_tokenizer = any(
            (snapshot / filename).is_file()
            for filename in ("tokenizer.json", "tokenizer_config.json")
        )
        has_weights = any(snapshot.glob("*.safetensors")) or any(snapshot.glob("*.bin"))
        if has_config and has_tokenizer and has_weights:
            return True
    return False


class LocalQwenService:
    """Local-only, serialized CPU inference using the approved Hugging Face model."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._tokenizer: Any = None
        self._model: Any = None
        self._torch: Any = None
        self._last_load_ms: int | None = None
        self._last_generation_ms: int | None = None
        self._last_error: str | None = None

    def _load_requirement_error(self) -> str | None:
        try:
            available_memory = _available_memory_bytes()
        except OSError:
            return "Available system memory could not be measured; model loading is blocked."
        if available_memory < MIN_AVAILABLE_MEMORY_BYTES:
            return "At least 1.0 GB of available system memory is required to load the local model."

        missing_packages = [
            package for package in ("torch", "transformers")
            if importlib.util.find_spec(package) is None
        ]
        if missing_packages:
            return "Required local model packages are not installed: " + ", ".join(missing_packages) + "."

        settings = get_settings()
        if _is_model_fully_cached(settings.llm_model_id):
            return None

        # Check if automated download is explicitly enabled
        settings = get_settings()
        allow_download = getattr(settings, "llm_allow_download", False) or (os.environ.get("LLM_ALLOW_DOWNLOAD", "").lower() in ("true", "1", "yes"))
        if not allow_download:
            return "Approved local model weights are not cached; downloads are disabled."

        try:
            cache_root = Path(
                os.environ.get("HUGGINGFACE_HUB_CACHE")
                or (Path(os.environ.get("HF_HOME", Path.home() / ".cache" / "huggingface")) / "hub")
            )
            cache_root.mkdir(parents=True, exist_ok=True)
            if shutil.disk_usage(cache_root).free < 2 * 1024**3:
                return "Insufficient disk space for model download (at least 2.0 GB required)."
        except Exception:
            pass

        return None

    def _load(self) -> None:
        if self._model is not None and self._tokenizer is not None:
            return
        requirement_error = self._load_requirement_error()
        if requirement_error:
            self._last_error = requirement_error
            raise AppError(
                code=ErrorCode.MODEL_UNAVAILABLE,
                message=f"The approved local language model is unavailable: {requirement_error}",
                http_status=503,
            )

        settings = get_settings()
        started = time.monotonic()
        try:
            import torch
            import transformers
            from transformers import AutoModelForCausalLM, AutoTokenizer

            is_cached = _is_model_fully_cached(settings.llm_model_id)

            # Pre-flight architecture and task validation
            if hasattr(transformers, "AutoConfig"):
                try:
                    config = transformers.AutoConfig.from_pretrained(
                        settings.llm_model_id,
                        local_files_only=is_cached,
                    )
                    architectures = getattr(config, "architectures", []) or []
                    if architectures and not any("CausalLM" in a or "LMHead" in a or "ForCausal" in a for a in architectures):
                        raise AppError(
                            code=ErrorCode.MODEL_UNAVAILABLE,
                            message=f"Model architecture '{architectures[0]}' is not supported for causal text generation.",
                            http_status=503,
                        )
                except AppError:
                    raise
                except Exception:
                    pass

            tokenizer = AutoTokenizer.from_pretrained(
                settings.llm_model_id,
                local_files_only=is_cached,
            )
            model = AutoModelForCausalLM.from_pretrained(
                settings.llm_model_id,
                torch_dtype="auto",
                local_files_only=is_cached,
            ).to("cpu")
            model.eval()
            self._tokenizer = tokenizer
            self._model = model
            self._torch = torch
            self._last_error = None
        except AppError:
            raise
        except Exception as exc:
            self._tokenizer = None
            self._model = None
            self._torch = None
            self._last_error = f"Local model initialization failed: {exc}"
            raise AppError(
                code=ErrorCode.MODEL_UNAVAILABLE,
                message=f"The approved local language model is unavailable: {exc}",
                http_status=503,
            ) from exc
        finally:
            self._last_load_ms = int((time.monotonic() - started) * 1000)

    def initialize(self) -> None:
        with self._lock:
            self._load()

    def health_status(self) -> dict[str, Any]:
        with self._lock:
            settings = get_settings()
            loaded = self._model is not None and self._tokenizer is not None
            issue = None if loaded else self._load_requirement_error()
            if loaded:
                try:
                    if _available_memory_bytes() < MIN_AVAILABLE_MEMORY_BYTES:
                        issue = "At least 1.0 GB of available system memory is required for inference."
                except OSError:
                    issue = "Available system memory could not be measured; inference is blocked."
            if loaded:
                state = "ok" if issue is None else "error"
                detail = issue
            else:
                state = "error"
                detail = issue or self._last_error or "The local model has not completed initialization."
            return {
                "status": state,
                "detail": detail,
                "meta": {
                    "model_id": settings.llm_model_id,
                    "loaded": loaded,
                    "device": "cpu",
                    "dtype": "checkpoint",
                    "last_load_ms": self._last_load_ms,
                    "last_generation_ms": self._last_generation_ms,
                },
            }

    def generate(self, system_prompt: str, user_prompt: str, *, max_new_tokens: int = 256) -> str:
        with self._lock:
            self._load()
            try:
                if _available_memory_bytes() < MIN_AVAILABLE_MEMORY_BYTES:
                    raise AppError(
                        code=ErrorCode.MODEL_UNAVAILABLE,
                        message="At least 1.0 GB of available system memory is required for inference.",
                        http_status=503,
                    )
                messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ]
                rendered = self._tokenizer.apply_chat_template(
                    messages,
                    add_generation_prompt=True,
                    tokenize=False,
                )
                encoded = self._tokenizer(
                    rendered,
                    return_tensors="pt",
                    truncation=True,
                    max_length=MAX_INPUT_TOKENS,
                )
                encoded = encoded.to("cpu")
                input_ids = encoded["input_ids"]
                configured_limit = max(
                    int(get_settings().llm_max_new_tokens_analysis),
                    1,
                )
                token_limit = min(max(int(max_new_tokens), 1), configured_limit, MAX_GENERATION_TOKENS)
                started = time.monotonic()
                with self._torch.inference_mode():
                    generated = self._model.generate(
                        input_ids,
                        do_sample=False,
                        max_new_tokens=token_limit,
                        pad_token_id=self._tokenizer.eos_token_id,
                    )
                self._last_generation_ms = int((time.monotonic() - started) * 1000)
                return self._tokenizer.decode(
                    generated[0, input_ids.shape[-1]:],
                    skip_special_tokens=True,
                ).strip()
            except AppError:
                raise
            except Exception as exc:
                self._last_error = "Local model inference failed."
                raise AppError(
                    code=ErrorCode.MODEL_UNAVAILABLE,
                    message="The approved local language model could not complete inference.",
                    http_status=503,
                ) from exc


_service = LocalQwenService()


def initialize() -> None:
    _service.initialize()


def health_status() -> dict[str, Any]:
    return _service.health_status()


def generate(system_prompt: str, user_prompt: str, *, max_new_tokens: int = 256) -> str:
    return _service.generate(system_prompt, user_prompt, max_new_tokens=max_new_tokens)
