from types import SimpleNamespace

import pytest

import evaluation.run_improved as improved


@pytest.mark.asyncio
async def test_improved_run_uses_required_configuration(
    monkeypatch,
):
    captured = {}

    class FakeClient:
        def list_examples(self, **kwargs):
            captured["dataset_name"] = kwargs[
                "dataset_name"
            ]
            return [
                SimpleNamespace(
                    inputs={"case_id": "HP-001"}
                )
            ]

        async def aevaluate(self, target, **kwargs):
            captured.update(kwargs)
            return "evaluation-result"

    monkeypatch.setattr(
        improved,
        "Client",
        lambda: FakeClient(),
    )

    result = await improved.run_improved()

    assert result == "evaluation-result"
    assert (
        captured["dataset_name"]
        == "incident-triage-golden-v1"
    )
    assert (
        captured["experiment_prefix"]
        == "incident-triage-improved"
    )
    assert (
        captured["metadata"]["agent_version"]
        == "week4-improved-v1"
    )
    assert captured["max_concurrency"] == 1
    assert len(captured["evaluators"]) == 5