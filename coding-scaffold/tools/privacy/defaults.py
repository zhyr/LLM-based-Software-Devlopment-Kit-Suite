"""
Privacy defaults aligned with HaxiTAG-AI-CMS KnowledgeBase / logger.

Sources:
- components/Admin/KnowledgeBase preprocess pipeline knobs
  (KnowledgeBuilder preprocess_options: 脱敏 / 去噪处理;
   SynthesisAugmentation_menu_config: 脱敏、去隐私化 / 去噪压缩)
- src/pages/api/workflow/knowledge-set/preprocess.ts :: anonymizeData
- src/utils/logger.ts :: SENSITIVE_KEYS + sanitize
"""

from __future__ import annotations

# Canonical pipeline ops (English ids). Chinese aliases map here.
PRIVACY_METHODS = ("clean", "denoise", "redact")

METHOD_ALIASES = {
    "清洗": "clean",
    "数据清洗": "clean",
    "clean": "clean",
    "去噪": "denoise",
    "去噪处理": "denoise",
    "去噪压缩": "denoise",
    "denoise": "denoise",
    "脱敏": "redact",
    "脱敏、去隐私化": "redact",
    "去隐私化": "redact",
    "redact": "redact",
    "anonymize": "redact",
}

# From logger.ts SENSITIVE_KEYS (substring match on object keys)
SENSITIVE_KEYS = [
    "password",
    "secret",
    "token",
    "key",
    "authorization",
    "apikey",
    "api_key",
    "access_token",
    "refresh_token",
    "connection_string",
    "mongodb_uri",
    "jwt_secret",
    "nextauth_secret",
    "private_key",
]

# From preprocess.ts anonymizeItem field keys
PII_FIELD_KEYS = ["email", "phone", "id"]

# Value-level regex (extended from preprocess card mask + Agent secret patterns)
DEFAULT_PII_PATTERNS = [
    # card-ish (preprocess.ts)
    r"\b\d{4}[\d-]{0,8}\d{4}\b",
    # email
    r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b",
    # CN mobile
    r"\b1[3-9]\d{9}\b",
    # CN ID (simple)
    r"\b[1-9]\d{5}(?:19|20)\d{2}(?:0[1-9]|1[0-2])(?:0[1-9]|[12]\d|3[01])\d{3}[\dXx]\b",
]

DEFAULT_SECRET_PATTERNS = [
    # Keep capture groups for safe replacement: group1=prefix group2=quote group3=value
    r"(?i)(api[_-]?key\s*[:=]\s*)(['\"]?)([A-Za-z0-9_\-]{16,})\2",
    r"(?i)(secret\s*[:=]\s*)(['\"]?)([^'\"\s,;]{8,})\2",
    r"(?i)(password\s*[:=]\s*)(['\"]?)([^'\"\s,;]{4,})\2",
    r"(?i)(access[_-]?token\s*[:=]\s*)(['\"]?)([A-Za-z0-9_\-.]{16,})\2",
    r"(?i)-----BEGIN (RSA |OPENSSH |EC )?PRIVATE KEY-----[\s\S]*?-----END (RSA |OPENSSH |EC )?PRIVATE KEY-----",
    r"(?i)\b(AKIA[0-9A-Z]{16})\b",
    r"\b(sk-[A-Za-z0-9]{20,})\b",
]

# Card numbers: 16 digits with optional separators (preprocess spirit, less greedy)
DEFAULT_CARD_PATTERN = r"\b(?:\d{4}[-\s]?){3}\d{4}\b"

# Denoise: treat these as context noise (aligned with KB「去噪压缩」意图，面向代码仓)
DEFAULT_NOISE_GLOBS = [
    "**/*.min.js",
    "**/*.min.css",
    "**/*.map",
    "**/package-lock.json",
    "**/pnpm-lock.yaml",
    "**/yarn.lock",
    "**/*.lock",
    "**/coverage/**",
    "**/__snapshots__/**",
    "**/*.snap",
]

SANITIZE_MAX_DEPTH = 10
REDACTED = "***REDACTED***"
PII_MASK = "***"
CARD_MASK = "****-****-****-****"
