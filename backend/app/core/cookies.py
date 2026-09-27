from fastapi import Response

ACCESS_TOKEN_COOKIE_NAME = "access_token"


def set_access_token_cookie(
    response: Response, *, token: str, max_age_seconds: int, secure: bool
) -> None:
    response.set_cookie(
        key=ACCESS_TOKEN_COOKIE_NAME,
        value=token,
        max_age=max_age_seconds,
        httponly=True,
        secure=secure,
        # Lax still attaches the cookie to same-site XHR/fetch (frontend and API
        # share a registrable domain in every deployment target here), while
        # refusing it on cross-site POST/PATCH/DELETE -- the main CSRF vector for
        # a cookie-authenticated API. See README "Design decisions" for the
        # full CSRF rationale.
        samesite="lax",
        path="/",
    )


def clear_access_token_cookie(response: Response, *, secure: bool) -> None:
    response.delete_cookie(
        key=ACCESS_TOKEN_COOKIE_NAME,
        httponly=True,
        secure=secure,
        samesite="lax",
        path="/",
    )
