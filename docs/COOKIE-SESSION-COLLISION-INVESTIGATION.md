# Cookie Session Collision Investigation

## Summary

Authorisations was vulnerable to a cross-subdomain cookie collision when another DBCA application set a cookie named `sessionid` on the parent domain `.dbca.wa.gov.au`. In browsers that serialise duplicate cookies in the opposite order from Chromium, the backend could receive the parent-domain session cookie last and reject the request, even though the user was already authenticated through SSO.

The immediate mitigation applied in this repository is to make Authorisations use a distinct host-scoped session cookie name, `authorisations_sessionid`, and to keep `SESSION_COOKIE_DOMAIN = None` so the browser does not scope the cookie to the parent domain.

## What We Observed

The reported failure mode was:

1. Authorisations sets a host-scoped session cookie for `authorisations.dbca.wa.gov.au`.
2. Another DBCA application on a sibling subdomain sets its own `sessionid` cookie on `.dbca.wa.gov.au`.
3. Firefox can send the two cookies in the order `authorisations.dbca.wa.gov.au` first, then `.dbca.wa.gov.au`.
4. Django keeps the last duplicate cookie value it sees in the request header.
5. Authorisations then sees the unrelated parent-domain value and treats the session as invalid.
6. The page can keep re-establishing a session, but API requests later fail with `403`.

I verified the parsing behaviour directly with Django's WSGI request handling. For duplicate `sessionid` cookies, the last one wins in `request.COOKIES`.

## Standards Research

The key normative source for HTTP cookies is RFC 6265, not a W3C Recommendation.

Relevant findings from RFC 6265:

- The Cookie header is defined by the IETF in RFC 6265.
- Servers should not rely on the serialisation order of cookies in the `Cookie` header.
- If two cookies share the same name but differ by path or domain, servers should not rely on which appears first.
- User agents are allowed to sort cookies by path length and creation time, but the document explicitly notes that not all user agents do so.

Relevant source links:

- RFC 6265: [https://www.rfc-editor.org/rfc/rfc6265](https://www.rfc-editor.org/rfc/rfc6265)
- W3C standards index: [https://www.w3.org/TR/](https://www.w3.org/TR/)
- W3C standards overview: [https://www.w3.org/standards/](https://www.w3.org/standards/)

Conclusion from the research:

- There is no W3C standard that mandates HTTP Cookie header ordering.
- The relevant cookie specification allows user-agent variability.
- This means the issue is not a standards violation by Firefox or Django in isolation.
- Authorisations must defend itself by avoiding a cookie-name collision that crosses trust boundaries.

## Reproduction

I reproduced the core parser behaviour with Django's WSGI request handling:

```python
from django.core.handlers.wsgi import WSGIRequest

req = WSGIRequest(environ_with_cookie_header)
print(req.COOKIES)
```

With duplicate cookie names, the later value wins. That makes the request outcome depend on user-agent ordering rather than application intent.

## Immediate Fix Applied

Files changed:

- [backend/config/settings.py](../backend/config/settings.py)
- [backend/e2e/tests/test_api_contracts.py](../backend/e2e/tests/test_api_contracts.py)

Behavioural change:

- `SESSION_COOKIE_NAME` now defaults to `authorisations_sessionid`.
- `SESSION_COOKIE_DOMAIN` is explicitly `None`.
- The application now includes regression tests that verify session stability when parent-domain cookies are present.

## Why This Fix Is Safe

This change avoids ambiguity entirely rather than trying to infer which duplicate cookie should be trusted. That is safer than attempting request-header parsing heuristics because:

- it does not depend on browser order,
- it does not depend on undocumented framework parsing details,
- it preserves existing SSO-based authentication,
- it keeps the session cookie host-scoped by design.

## Critical Limitation: No "Perfect Fix" Exists

**This fix eliminates the immediate collision with a sibling `sessionid` cookie, but it does not solve the underlying risk of cross-subdomain cookie collisions organisation-wide.**

Why:

1. **Any sibling application can still set a parent-domain cookie** with a generic name (`sessionid`, `PHPSESSID`, etc.) and interfere with any other application.

2. **Prefix-based naming delays but does not eliminate the risk.** If a new application is built and also uses `authorisations_sessionid` on the parent domain, the collision recurs.

3. **Host-scoping only protects if applications honour it.** If another application sets `authorisations_sessionid` on `.dbca.wa.gov.au`, the browser will still send it to this application.

**The only organisation-level solution is policy:**

- Establish and enforce unique, application-prefixed cookie names across DBCA services.
- Make host-scoping the default posture for authentication cookies unless there is a documented exception.
- Require cross-team review of any cookie that targets a parent domain.
- Raise developer awareness during onboarding so teams do not accidentally reintroduce similar collisions.
