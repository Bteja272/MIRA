from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from prometheus_client import REGISTRY

import app.api.routes.query as query_route
import app.services.langgraph_agent_service as agent_service

from app.core.metrics import render_metrics
from app.main import app


def _sample_value(
    name: str,
    labels: dict[str, str],
) -> float:
    value = REGISTRY.get_sample_value(
        name,
        labels,
    )

    if value is None:
        return 0.0

    return float(value)


def test_metrics_endpoint_returns_prometheus_format():
    client = TestClient(
        app,
        base_url="http://localhost",
    )

    response = client.get(
        "/metrics"
    )

    assert response.status_code == 200

    content_type = response.headers.get(
        "content-type",
        "",
    )

    assert "text/plain" in content_type

    assert (
        "mira_agent_requests_total"
        in response.text
    )


def test_safety_guard_metric_increments():
    labels = {
        "outcome": "allowed",
        "category": "allowed",
    }

    before = _sample_value(
        "mira_safety_guard_total",
        labels,
    )

    result = agent_service.safety_node(
        {
            "query": "What is hemoglobin?",
        }
    )

    after = _sample_value(
        "mira_safety_guard_total",
        labels,
    )

    assert (
        result["safety_status"]
        == "allowed"
    )

    assert after == before + 1


def test_agent_route_metric_increments(
    monkeypatch,
):
    labels = {
        "route": "direct",
    }

    before = _sample_value(
        "mira_agent_requests_total",
        labels,
    )

    monkeypatch.setattr(
        agent_service.agent_graph,
        "invoke",
        lambda state: {
            "route": "direct",
            "result": {
                "answer": (
                    "Synthetic answer."
                ),
                "sources": [],
            },
            "safety_status": "allowed",
        },
    )

    result = (
        agent_service
        .LangGraphAgentService
        .query(
            query="What is hemoglobin?",
        )
    )

    after = _sample_value(
        "mira_agent_requests_total",
        labels,
    )

    assert result["route"] == "direct"
    assert after == before + 1


def test_query_route_metric_increments(
    monkeypatch,
):
    labels = {
        "route": "direct",
    }

    before = _sample_value(
        "mira_query_requests_total",
        labels,
    )

    monkeypatch.setattr(
        query_route.ConversationMemoryService,
        "build_retrieval_query",
        lambda **kwargs: kwargs["query"],
    )

    monkeypatch.setattr(
        query_route.LangGraphAgentService,
        "query",
        lambda **kwargs: {
            "query": kwargs["query"],
            "answer": (
                "Synthetic answer."
            ),
            "route": "direct",
            "document_id": None,
            "document_ids": [],
            "selected_document_count": 0,
            "sources": [],
        },
    )

    monkeypatch.setattr(
        query_route.ConversationService,
        "persist_exchange",
        lambda **kwargs: (
            "conversation-test",
            "message-test",
        ),
    )

    request = SimpleNamespace(
        query="What is hemoglobin?",
        document_ids=[],
        conversation_id=None,
    )

    current_user = SimpleNamespace(
        user_id="synthetic-user",
    )

    result = query_route.query_agent(
        request=request,
        current_user=current_user,
    )

    after = _sample_value(
        "mira_query_requests_total",
        labels,
    )

    assert result["route"] == "direct"
    assert after == before + 1


def test_validation_failure_metric_increments(
    monkeypatch,
):
    labels = {
        "stage": "validation",
    }

    before = _sample_value(
        "mira_query_failures_total",
        labels,
    )

    monkeypatch.setattr(
        query_route.DocumentService,
        "get_existing_document_ids",
        lambda **kwargs: [],
    )

    request = SimpleNamespace(
        query="Summarize this document.",
        document_ids=[
            "synthetic-document-id",
        ],
        conversation_id=None,
    )

    current_user = SimpleNamespace(
        user_id="synthetic-user",
    )

    with pytest.raises(
        HTTPException
    ) as exc_info:
        query_route.query_agent(
            request=request,
            current_user=current_user,
        )

    after = _sample_value(
        "mira_query_failures_total",
        labels,
    )

    assert (
        exc_info.value.status_code
        == 404
    )

    assert after == before + 1


def test_prometheus_labels_do_not_contain_sensitive_values():
    sensitive_values = (
        "synthetic.person@example.com",
        "private-lab-report.pdf",
        "document-secret-id",
        "conversation-secret-id",
        "my glucose result is 500",
    )

    rendered = (
        render_metrics()
        .decode("utf-8")
    )

    for sensitive_value in (
        sensitive_values
    ):
        assert (
            sensitive_value
            not in rendered
        )