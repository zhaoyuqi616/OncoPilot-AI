from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from typing import Iterable

from fastapi import Depends, Header, HTTPException, status

from oncopilot_ai.config import settings


@dataclass(frozen=True)
class AuthContext:
    user_id: str
    workspace_id: str
    roles: frozenset[str]
    scopes: frozenset[str] = frozenset()

    @property
    def is_admin(self) -> bool:
        return bool(self.roles & {"admin", "oncopilot_admin"})


_PROMPT_INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?previous\s+instructions",
    r"system\s+prompt",
    r"developer\s+message",
    r"reveal\s+(the\s+)?prompt",
    r"follow\s+these\s+instructions\s+instead",
    r"do\s+not\s+follow\s+the\s+user",
]


def stable_hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]


def detect_prompt_injection(text: str) -> bool:
    lowered = text.lower()
    return any(re.search(pattern, lowered) for pattern in _PROMPT_INJECTION_PATTERNS)


def can_access_chunk(chunk: dict, auth: AuthContext) -> bool:
    """Enforce workspace + optional role/user ACLs before text reaches agents/LLM."""
    if str(chunk.get("workspace_id", "")) != auth.workspace_id:
        return False
    allowed_users = {str(x) for x in chunk.get("allowed_users", []) if str(x)}
    allowed_roles = {str(x) for x in chunk.get("allowed_roles", []) if str(x)}
    if allowed_users and auth.user_id not in allowed_users and not auth.is_admin:
        return False
    if allowed_roles and not (allowed_roles & set(auth.roles)) and not auth.is_admin:
        return False
    return True


def has_sensitive_content(chunks: Iterable[dict]) -> bool:
    sensitive = settings.sensitive_label_set
    return any(str(c.get("sensitivity", "internal")).lower() in sensitive for c in chunks)


def external_llm_allowed(chunks: Iterable[dict]) -> bool:
    return settings.allow_external_llm_for_sensitive or not has_sensitive_content(chunks)


def _decode_jwt(token: str) -> dict:
    try:
        import jwt
        from jwt import PyJWKClient
    except ImportError as exc:  # pragma: no cover
        raise HTTPException(status_code=500, detail="JWT support is not installed") from exc

    if not (settings.jwt_jwks_url and settings.jwt_issuer and settings.jwt_audience):
        raise HTTPException(status_code=500, detail="JWT issuer/audience/JWKS are not configured")
    try:
        signing_key = PyJWKClient(settings.jwt_jwks_url).get_signing_key_from_jwt(token)
        return jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256", "ES256"],
            audience=settings.jwt_audience,
            issuer=settings.jwt_issuer,
        )
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid access token") from exc


def get_current_user(
    authorization: str | None = Header(default=None),
    x_user_id: str | None = Header(default=None),
    x_workspace_id: str | None = Header(default=None),
    x_roles: str | None = Header(default=None),
) -> AuthContext:
    if settings.auth_mode == "jwt":
        if not authorization or not authorization.lower().startswith("bearer "):
            raise HTTPException(status_code=401, detail="Bearer token required")
        claims = _decode_jwt(authorization.split(" ", 1)[1].strip())
        user_id = str(claims.get("sub") or "")
        workspace_id = str(claims.get("workspace_id") or claims.get("tenant_id") or "")
        roles_claim = claims.get("roles", [])
        roles = {str(x) for x in roles_claim} if isinstance(roles_claim, list) else {str(roles_claim)}
        scopes_claim = str(claims.get("scope", "")).split()
        if not user_id or not workspace_id:
            raise HTTPException(status_code=403, detail="Token is missing required identity/workspace claims")
        return AuthContext(user_id=user_id, workspace_id=workspace_id, roles=frozenset(roles), scopes=frozenset(scopes_claim))

    # Local development only. Production readiness endpoint rejects dev auth in production.
    return AuthContext(
        user_id=x_user_id or "local-user",
        workspace_id=x_workspace_id or "default",
        roles=frozenset(r.strip() for r in (x_roles or "researcher").split(",") if r.strip()),
    )


def require_ingestor(auth: AuthContext = Depends(get_current_user)) -> AuthContext:
    if not (auth.is_admin or auth.roles & {"ingestor", "data_steward"}):
        raise HTTPException(status_code=403, detail="Ingestor or admin role required")
    return auth
