"""Error classification for user-friendly messages."""

from dataclasses import dataclass
from typing import Optional

@dataclass
class ClassifiedError:
    code: str
    message: str
    hint: str
    retryable: bool
    status: int
    
    def as_dict(self) -> dict:
        return {
            "code": self.code,
            "message": self.message,
            "hint": self.hint,
            "retryable": self.retryable,
        }

def classify(exc: Exception) -> ClassifiedError:
    """Classify exception into user-friendly error."""
    
    err_str = str(exc).lower()
    
    # Google errors
    if "api key" in err_str or "authentication" in err_str:
        return ClassifiedError(
            code="AUTH_ERROR",
            message="Authentication failed with Google AI.",
            hint="Check your GOOGLE_API_KEY in the .env file.",
            retryable=False,
            status=401
        )
    
    if "quota" in err_str:
        return ClassifiedError(
            code="QUOTA_EXCEEDED",
            message="Google AI quota exceeded.",
            hint="Check your usage at https://console.cloud.google.com/apis/",
            retryable=False,
            status=402
        )
    
    # GMICloud errors
    if "gmi" in err_str and "key" in err_str:
        return ClassifiedError(
            code="GMI_AUTH_ERROR",
            message="GMICloud authentication failed.",
            hint="Check your GMI_API_KEY in the .env file.",
            retryable=False,
            status=401
        )
    
    # Rate limits
    if "rate limit" in err_str or "429" in err_str:
        return ClassifiedError(
            code="RATE_LIMIT",
            message="Rate limit exceeded. Please wait and try again.",
            hint="The AI service is experiencing high demand. Try again in a few minutes.",
            retryable=True,
            status=429
        )
    
    # Timeouts
    if "timeout" in err_str:
        return ClassifiedError(
            code="TIMEOUT",
            message="Request timed out.",
            hint="Try with a shorter video or simpler prompt.",
            retryable=True,
            status=504
        )
    
    # Fallback
    return ClassifiedError(
        code="UNKNOWN_ERROR",
        message="Something went wrong while generating your video.",
        hint="Please try again or contact support if the issue persists.",
        retryable=True,
        status=500
    )