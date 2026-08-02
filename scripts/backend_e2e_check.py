from __future__ import annotations

import argparse
import json
import sys
import tempfile
import time
from pathlib import Path
from uuid import uuid4

import httpx


SYNTHETIC_DOCUMENT = """
SYNTHETIC DISCHARGE SUMMARY

Patient: Batch TwoG Patient
Attending Physician: Dr. Example

Diagnoses:
1. Hypertension

Medications:
Lisinopril 10 mg by mouth once daily.

Follow-up:
Schedule a primary-care follow-up appointment within two weeks.
""".strip()


class CheckFailure(RuntimeError):
    pass


def require(
    condition: bool,
    message: str,
) -> None:
    if not condition:
        raise CheckFailure(message)


def require_status(
    response: httpx.Response,
    expected: int,
    label: str,
) -> None:
    if response.status_code != expected:
        raise CheckFailure(
            (
                f"{label} returned "
                f"{response.status_code}; "
                f"expected {expected}.\n"
                f"Response: {response.text}"
            )
        )


def register_user(
    client: httpx.Client,
    email: str,
    password: str,
) -> None:
    response = client.post(
        "/auth/register",
        json={
            "email": email,
            "password": password,
        },
    )

    require_status(
        response,
        201,
        "register",
    )


def login_user(
    client: httpx.Client,
    email: str,
    password: str,
) -> str:
    response = client.post(
        "/auth/login",
        data={
            "username": email,
            "password": password,
        },
    )

    require_status(
        response,
        200,
        "login",
    )

    payload = response.json()
    token = payload.get(
        "access_token"
    )

    require(
        isinstance(token, str)
        and bool(token),
        "Login did not return an access token.",
    )

    return token


def auth_headers(
    token: str,
) -> dict[str, str]:
    return {
        "Authorization": (
            f"Bearer {token}"
        )
    }


def print_step(
    label: str,
    payload=None,
) -> None:
    print(f"[PASS] {label}")

    if payload is not None:
        print(
            json.dumps(
                payload,
                indent=2,
                default=str,
            )
        )


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Run MIRA backend end-to-end checks "
            "against a live API."
        )
    )

    parser.add_argument(
        "--base-url",
        default="http://127.0.0.1:8001",
    )

    parser.add_argument(
        "--include-llm",
        action="store_true",
        help=(
            "Also run document RAG and structured "
            "extraction checks."
        ),
    )

    parser.add_argument(
        "--replace-extraction",
        action="store_true",
        help=(
            "Regenerate and replace the extraction. "
            "Requires --include-llm."
        ),
    )

    args = parser.parse_args()

    suffix = uuid4().hex[:12]

    email_a = (
        f"batch2g-a-{suffix}@example.com"
    )

    email_b = (
        f"batch2g-b-{suffix}@example.com"
    )

    password = (
        "Batch2G-Synthetic-Password-2026!"
    )

    document_id: str | None = None

    with tempfile.TemporaryDirectory() as tmp:
        document_path = (
            Path(tmp)
            / "synthetic_discharge_summary.txt"
        )

        document_path.write_text(
            SYNTHETIC_DOCUMENT,
            encoding="utf-8",
        )

        timeout = httpx.Timeout(
            connect=10.0,
            read=300.0,
            write=30.0,
            pool=10.0,
        )

        with httpx.Client(
            base_url=args.base_url,
            timeout=timeout,
        ) as client:
            try:
                response = client.get(
                    "/health"
                )

                require_status(
                    response,
                    200,
                    "health",
                )

                print_step(
                    "API liveness",
                    response.json(),
                )

                register_user(
                    client,
                    email_a,
                    password,
                )

                register_user(
                    client,
                    email_b,
                    password,
                )

                print_step(
                    "Two test users registered"
                )

                duplicate_registration = (
                    client.post(
                        "/auth/register",
                        json={
                            "email": email_a,
                            "password": password,
                        },
                    )
                )

                require_status(
                    duplicate_registration,
                    409,
                    "duplicate registration",
                )

                print_step(
                    "Duplicate registration rejected"
                )

                token_a = login_user(
                    client,
                    email_a,
                    password,
                )

                token_b = login_user(
                    client,
                    email_b,
                    password,
                )

                headers_a = auth_headers(
                    token_a
                )

                headers_b = auth_headers(
                    token_b
                )

                me_response = client.get(
                    "/auth/me",
                    headers=headers_a,
                )

                require_status(
                    me_response,
                    200,
                    "auth/me",
                )

                require(
                    me_response.json().get(
                        "email"
                    ) == email_a,
                    "/auth/me returned the wrong user.",
                )

                print_step(
                    "Authenticated account lookup"
                )

                invalid_token_response = (
                    client.get(
                        "/auth/me",
                        headers=auth_headers(
                            "invalid-token"
                        ),
                    )
                )

                require_status(
                    invalid_token_response,
                    401,
                    "invalid token",
                )

                print_step(
                    "Invalid token rejected"
                )

                with document_path.open(
                    "rb"
                ) as handle:
                    upload_response = (
                        client.post(
                            "/ingest",
                            headers=headers_a,
                            files={
                                "file": (
                                    document_path.name,
                                    handle,
                                    "text/plain",
                                )
                            },
                        )
                    )

                require_status(
                    upload_response,
                    200,
                    "document upload",
                )

                upload_payload = (
                    upload_response.json()
                )

                require(
                    upload_payload.get(
                        "duplicate"
                    ) is False,
                    "Initial upload was marked duplicate.",
                )

                document_id = (
                    upload_payload.get(
                        "document_id"
                    )
                )

                require(
                    isinstance(
                        document_id,
                        str,
                    )
                    and bool(document_id),
                    "Upload did not return document_id.",
                )

                print_step(
                    "Document uploaded",
                    upload_payload,
                )

                with document_path.open(
                    "rb"
                ) as handle:
                    duplicate_upload = (
                        client.post(
                            "/ingest",
                            headers=headers_a,
                            files={
                                "file": (
                                    document_path.name,
                                    handle,
                                    "text/plain",
                                )
                            },
                        )
                    )

                require_status(
                    duplicate_upload,
                    200,
                    "duplicate upload",
                )

                duplicate_payload = (
                    duplicate_upload.json()
                )

                require(
                    duplicate_payload.get(
                        "duplicate"
                    ) is True,
                    "Duplicate upload was not detected.",
                )

                require(
                    duplicate_payload.get(
                        "existing_document_id"
                    ) == document_id,
                    "Duplicate response returned wrong document.",
                )

                print_step(
                    "Per-user duplicate detection"
                )

                list_response = client.get(
                    "/documents",
                    headers=headers_a,
                )

                require_status(
                    list_response,
                    200,
                    "document list",
                )

                listed_ids = {
                    document["document_id"]
                    for document in (
                        list_response.json()
                        .get("documents", [])
                    )
                }

                require(
                    document_id in listed_ids,
                    "Uploaded document missing from list.",
                )

                print_step(
                    "Owned document list"
                )

                cross_user_get = client.get(
                    f"/documents/{document_id}",
                    headers=headers_b,
                )

                require_status(
                    cross_user_get,
                    404,
                    "cross-user document get",
                )

                cross_user_delete = (
                    client.delete(
                        f"/documents/{document_id}",
                        headers=headers_b,
                    )
                )

                require_status(
                    cross_user_delete,
                    404,
                    "cross-user document delete",
                )

                cross_user_extract = (
                    client.post(
                        (
                            f"/documents/"
                            f"{document_id}/extract"
                        ),
                        headers=headers_b,
                        json={
                            "replace_existing": False
                        },
                    )
                )

                require_status(
                    cross_user_extract,
                    404,
                    "cross-user extraction",
                )

                print_step(
                    "Cross-user isolation"
                )

                if args.include_llm:
                    query_response = (
                        client.post(
                            "/query",
                            headers=headers_a,
                            json={
                                "query": (
                                    "What medication is listed "
                                    "in this document?"
                                ),
                                "document_ids": [
                                    document_id
                                ],
                            },
                        )
                    )

                    require_status(
                        query_response,
                        200,
                        "document RAG query",
                    )

                    query_payload = (
                        query_response.json()
                    )

                    require(
                        query_payload.get(
                            "route"
                        ) == "rag",
                        "Document query did not use RAG.",
                    )

                    require(
                        query_payload.get(
                            "selected_document_count"
                        ) == 1,
                        "Document query selection metadata is wrong.",
                    )

                    print_step(
                        "Document-grounded RAG",
                        query_payload,
                    )

                    extraction_response = (
                        client.post(
                            (
                                f"/documents/"
                                f"{document_id}/extract"
                            ),
                            headers=headers_a,
                            json={
                                "replace_existing": False
                            },
                        )
                    )

                    require_status(
                        extraction_response,
                        200,
                        "structured extraction",
                    )

                    extraction_payload = (
                        extraction_response.json()
                    )

                    require(
                        extraction_payload.get(
                            "cached"
                        ) is False,
                        "Initial extraction was unexpectedly cached.",
                    )

                    extraction_id = (
                        extraction_payload
                        .get("result", {})
                        .get("extraction_id")
                    )

                    require(
                        isinstance(
                            extraction_id,
                            str,
                        )
                        and bool(extraction_id),
                        "Extraction ID missing.",
                    )

                    print_step(
                        "Structured extraction generated"
                    )

                    cached_response = (
                        client.post(
                            (
                                f"/documents/"
                                f"{document_id}/extract"
                            ),
                            headers=headers_a,
                            json={
                                "replace_existing": False
                            },
                        )
                    )

                    require_status(
                        cached_response,
                        200,
                        "cached extraction",
                    )

                    cached_payload = (
                        cached_response.json()
                    )

                    require(
                        cached_payload.get(
                            "cached"
                        ) is True,
                        "Second extraction was not cached.",
                    )

                    require(
                        (
                            cached_payload
                            .get("result", {})
                            .get("extraction_id")
                        )
                        == extraction_id,
                        "Cached extraction ID changed.",
                    )

                    print_step(
                        "Structured extraction cache"
                    )

                    get_extraction = client.get(
                        (
                            f"/documents/"
                            f"{document_id}/extraction"
                        ),
                        headers=headers_a,
                    )

                    require_status(
                        get_extraction,
                        200,
                        "get extraction",
                    )

                    print_step(
                        "Stored extraction retrieved"
                    )

                    if args.replace_extraction:
                        previous_updated_at = (
                            cached_payload
                            .get("result", {})
                            .get("updated_at")
                        )

                        time.sleep(0.01)

                        replace_response = (
                            client.post(
                                (
                                    f"/documents/"
                                    f"{document_id}/extract"
                                ),
                                headers=headers_a,
                                json={
                                    "replace_existing": True
                                },
                            )
                        )

                        require_status(
                            replace_response,
                            200,
                            "replace extraction",
                        )

                        replace_payload = (
                            replace_response.json()
                        )

                        require(
                            replace_payload.get(
                                "replaced"
                            ) is True,
                            "Extraction was not marked replaced.",
                        )

                        require(
                            (
                                replace_payload
                                .get("result", {})
                                .get("extraction_id")
                            )
                            == extraction_id,
                            "Replacement changed extraction ID.",
                        )

                        require(
                            (
                                replace_payload
                                .get("result", {})
                                .get("updated_at")
                            )
                            != previous_updated_at,
                            "Replacement did not update updated_at.",
                        )

                        print_step(
                            "Structured extraction replacement"
                        )

                delete_response = client.delete(
                    f"/documents/{document_id}",
                    headers=headers_a,
                )

                require_status(
                    delete_response,
                    200,
                    "document delete",
                )

                require(
                    delete_response.json().get(
                        "deleted"
                    ) is True,
                    "Document deletion was not confirmed.",
                )

                print_step(
                    "Permanent document deletion",
                    delete_response.json(),
                )

                document_id = None

                missing_document = client.get(
                    (
                        f"/documents/"
                        f"{upload_payload['document_id']}"
                    ),
                    headers=headers_a,
                )

                require_status(
                    missing_document,
                    404,
                    "deleted document lookup",
                )

                if args.include_llm:
                    missing_extraction = (
                        client.get(
                            (
                                f"/documents/"
                                f"{upload_payload['document_id']}"
                                "/extraction"
                            ),
                            headers=headers_a,
                        )
                    )

                    require_status(
                        missing_extraction,
                        404,
                        "cascaded extraction lookup",
                    )

                    print_step(
                        "Extraction cascade deletion"
                    )

                print(
                    "\nBatch 2G backend E2E check passed."
                )

                return 0

            except (
                httpx.HTTPError,
                CheckFailure,
            ) as exc:
                print(
                    f"\n[FAIL] {exc}",
                    file=sys.stderr,
                )

                return 1

            finally:
                if document_id is not None:
                    try:
                        client.delete(
                            (
                                f"/documents/"
                                f"{document_id}"
                            ),
                            headers=locals().get(
                                "headers_a",
                                {},
                            ),
                        )
                    except Exception:
                        pass


if __name__ == "__main__":
    raise SystemExit(main())