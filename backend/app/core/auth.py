import base64
import json
import logging
import time
from typing import Optional, Dict, Any
from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from jwt import PyJWKClient, PyJWTError
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.core.database import get_db
from backend.app.models.agent import AgentProfile

logger = logging.getLogger("complaint_assistant.auth")

# FastAPI security scheme
security = HTTPBearer(auto_error=False)

# Cached JWKS client
_jwks_client: Optional[PyJWKClient] = None


def get_jwks_url() -> Optional[str]:
    """Resolve JWKS URL from explicit config, issuer, or publishable key."""
    if settings.CLERK_JWKS_URL:
        return settings.CLERK_JWKS_URL.strip()

    if settings.CLERK_ISSUER:
        issuer = settings.CLERK_ISSUER.strip().rstrip("/")
        return f"{issuer}/.well-known/jwks.json"

    if settings.CLERK_PUBLISHABLE_KEY:
        try:
            pub_key = settings.CLERK_PUBLISHABLE_KEY.strip()
            # Clerk publishable keys format: pk_test_<base64_encoded_domain>$ or pk_live_...
            prefix = "pk_test_" if pub_key.startswith("pk_test_") else "pk_live_" if pub_key.startswith("pk_live_") else ""
            if prefix:
                encoded = pub_key[len(prefix):]
                # Pad if needed
                padded = encoded + "=" * (-len(encoded) % 4)
                domain = base64.b64decode(padded).decode("utf-8").strip().rstrip("$")
                return f"https://{domain}/.well-known/jwks.json"
        except Exception as exc:
            logger.warning("Could not derive JWKS URL from CLERK_PUBLISHABLE_KEY: %s", exc)

    return None


def get_clerk_issuer() -> Optional[str]:
    """Resolve expected Clerk issuer URL from explicit config, JWKS URL, or publishable key."""
    if settings.CLERK_ISSUER:
        return settings.CLERK_ISSUER.strip().rstrip("/")

    if settings.CLERK_JWKS_URL:
        url = settings.CLERK_JWKS_URL.strip()
        idx = url.find("/.well-known")
        if idx != -1:
            return url[:idx].rstrip("/")

    if settings.CLERK_PUBLISHABLE_KEY:
        try:
            pub_key = settings.CLERK_PUBLISHABLE_KEY.strip()
            prefix = "pk_test_" if pub_key.startswith("pk_test_") else "pk_live_" if pub_key.startswith("pk_live_") else ""
            if prefix:
                encoded = pub_key[len(prefix):]
                padded = encoded + "=" * (-len(encoded) % 4)
                domain = base64.b64decode(padded).decode("utf-8").strip().rstrip("$")
                return f"https://{domain}"
        except Exception:
            pass

    return None


def format_pem_public_key(raw_key: Optional[str]) -> Optional[str]:
    """Clean, unescape, and structure PEM public key from environment variable."""
    if not raw_key or not raw_key.strip():
        return None
    key = raw_key.strip().strip("'\"")
    # Replace literal escaped newlines with real newlines
    key = key.replace("\\n", "\n").replace("\\r", "\r")

    header = "-----BEGIN PUBLIC KEY-----"
    footer = "-----END PUBLIC KEY-----"
    if header in key and footer in key:
        start = key.find(header) + len(header)
        end = key.find(footer)
        body = "".join(key[start:end].split())
        lines = [body[i:i + 64] for i in range(0, len(body), 64)]
        return f"{header}\n" + "\n".join(lines) + f"\n{footer}"

    # If raw base64 without headers
    clean_body = "".join(key.split())
    lines = [clean_body[i:i + 64] for i in range(0, len(clean_body), 64)]
    return f"{header}\n" + "\n".join(lines) + f"\n{footer}"


def get_jwks_client() -> Optional[PyJWKClient]:
    """Retrieve or initialize singleton JWKS client."""
    global _jwks_client
    url = get_jwks_url()
    if url:
        if _jwks_client is None or _jwks_client.uri != url:
            _jwks_client = PyJWKClient(url, cache_jwk_set=True, lifespan=3600)
        return _jwks_client
    return None


class ClerkTokenVerifier:
    """Verifies Clerk JWT tokens against cryptographic keys."""

    @staticmethod
    def verify_token(token: str) -> Dict[str, Any]:
        """
        Verify Clerk JWT token signature, expiration, issuer, and authorized party.
        Supports:
        1. Remote JWKS endpoint (CLERK_JWKS_URL, CLERK_ISSUER, or derived from CLERK_PUBLISHABLE_KEY) [Preferred]
        2. PEM public key (CLERK_JWT_KEY)
        3. Test / development bypass tokens for isolated unit testing
        """
        if not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication token is missing.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # 1. Inspect unverified headers to determine algorithm and key ID
        try:
            unverified_headers = jwt.get_unverified_header(token)
            unverified_claims = jwt.decode(token, options={"verify_signature": False})
        except PyJWTError as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Malformed authentication token: {exc}",
                headers={"WWW-Authenticate": "Bearer"},
            )

        alg = unverified_headers.get("alg", "RS256")
        expected_issuer = get_clerk_issuer()

        # 2. Support explicit test tokens in non-production environments
        if (
            (settings.ENVIRONMENT in ("testing", "development") or not settings.is_clerk_configured)
            and unverified_claims.get("iss") == "clerk-test-issuer"
        ):
            # Test token validation
            now = time.time()
            if unverified_claims.get("exp", 0) < now:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication token has expired.",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            return unverified_claims

        # 3. Verify signature using PyJWKClient (JWKS) - Preferred approach
        jwks = get_jwks_client()
        jwks_error: Optional[Exception] = None
        if jwks:
            try:
                signing_key = jwks.get_signing_key_from_jwt(token)
                kwargs: Dict[str, Any] = {
                    "algorithms": [alg],
                    "options": {"verify_aud": False},
                }
                if expected_issuer:
                    kwargs["issuer"] = expected_issuer

                payload = jwt.decode(token, signing_key.key, **kwargs)

                # Validate authorized party if specified
                if settings.CLERK_AUTHORIZED_PARTY and payload.get("azp"):
                    if payload["azp"] != settings.CLERK_AUTHORIZED_PARTY:
                        raise HTTPException(
                            status_code=status.HTTP_403_FORBIDDEN,
                            detail="Token authorized party mismatch.",
                        )

                return payload
            except jwt.ExpiredSignatureError:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication token has expired.",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            except HTTPException:
                raise
            except Exception as exc:
                logger.warning("JWKS verification error: %s", exc)
                jwks_error = exc

        # 4. Verify signature using PEM Public Key if configured
        if settings.CLERK_JWT_KEY:
            try:
                public_key = format_pem_public_key(settings.CLERK_JWT_KEY)
                if not public_key:
                    raise PyJWTError("Could not parse the provided public key.")

                kwargs = {
                    "algorithms": [alg],
                    "options": {"verify_aud": False},
                }
                if expected_issuer:
                    kwargs["issuer"] = expected_issuer

                payload = jwt.decode(token, public_key, **kwargs)

                # Validate authorized party if specified
                if settings.CLERK_AUTHORIZED_PARTY and payload.get("azp"):
                    if payload["azp"] != settings.CLERK_AUTHORIZED_PARTY:
                        raise HTTPException(
                            status_code=status.HTTP_403_FORBIDDEN,
                            detail="Token authorized party mismatch.",
                        )

                return payload
            except jwt.ExpiredSignatureError:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication token has expired.",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            except HTTPException:
                raise
            except PyJWTError as exc:
                logger.warning("PEM key verification error: %s", exc)
                if jwks_error:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail=f"Token verification failed against Clerk JWKS ({jwks_error}) and PEM key ({exc}).",
                        headers={"WWW-Authenticate": "Bearer"},
                    )
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=f"Invalid token signature: {exc}",
                    headers={"WWW-Authenticate": "Bearer"},
                )

        # If JWKS was attempted but failed, and no PEM key was configured
        if jwks_error:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Token verification failed against Clerk JWKS: {jwks_error}",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # 5. In local development sandbox mode with unconfigured keys, fallback to decoding payload
        if not settings.is_clerk_configured and settings.ENVIRONMENT in ("development", "testing"):
            now = time.time()
            if unverified_claims.get("exp") and unverified_claims["exp"] < now:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication token has expired.",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            return unverified_claims

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Clerk authentication keys are unconfigured on the server.",
        )


def get_current_clerk_claims(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security),
) -> Dict[str, Any]:
    """FastAPI dependency: Extract and verify Clerk JWT claims."""
    if not credentials or not credentials.credentials:
        if not settings.AUTH_ENABLED:
            return {
                "sub": "dev_agent_default",
                "name": "Support Agent",
                "email": "agent@support.internal",
            }
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please provide a Bearer session token.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return ClerkTokenVerifier.verify_token(credentials.credentials)


def get_current_agent(
    claims: Dict[str, Any] = Depends(get_current_clerk_claims),
    db: Session = Depends(get_db),
) -> AgentProfile:
    """
    FastAPI dependency: Authenticate support agent, resolve database profile,
    and enforce active account status. Auto-provisions new profiles with 'support_agent'
    role (never 'supervisor').
    """
    clerk_user_id = claims.get("sub")
    if not clerk_user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token is missing required subject claim (sub).",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Lookup existing agent profile
    agent = db.query(AgentProfile).filter(AgentProfile.clerk_user_id == clerk_user_id).first()

    if not agent:
        # Extract metadata from token claims
        email = claims.get("email") or claims.get("email_address")
        if not email:
            email_addresses = claims.get("email_addresses", [])
            if email_addresses and isinstance(email_addresses, list):
                first_email = email_addresses[0]
                email = first_email.get("email_address") if isinstance(first_email, dict) else str(first_email)

        if not email:
            email = f"{clerk_user_id}@agent.internal"

        name = claims.get("name") or claims.get("display_name")
        if not name:
            first_name = claims.get("first_name", "")
            last_name = claims.get("last_name", "")
            name = f"{first_name} {last_name}".strip() or email.split("@")[0]

        # Invariant: Auto-provisioned profiles NEVER receive supervisor role
        agent = AgentProfile(
            clerk_user_id=clerk_user_id,
            email=email,
            display_name=name,
            role="support_agent",
            is_active=True,
        )
        db.add(agent)
        db.commit()
        db.refresh(agent)
        logger.info("Auto-provisioned new support agent profile: %s (%s)", agent.display_name, agent.id)

    # Enforce active account status
    if not agent.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Agent account has been deactivated. Please contact your supervisor.",
        )

    return agent


def require_supervisor(
    current_agent: AgentProfile = Depends(get_current_agent),
) -> AgentProfile:
    """FastAPI dependency: Enforce supervisor role permissions."""
    if current_agent.role != "supervisor":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Unauthorized: Supervisor privileges required for this action.",
        )
    return current_agent
