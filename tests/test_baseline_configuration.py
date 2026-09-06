from types import SimpleNamespace

import pytest

import evaluation.run_baseline as baseline


@pytest.mark.asyncio
async def test_baseline_uses_required_configuration(
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
            captured["target"] = target
            captured.update(kwargs)
            return "evaluation-result"

    monkeypatch.setattr(
        baseline,
        "Client",
        lambda: FakeClient(),
    )

    result = await baseline.run_baseline()

    assert result == "evaluation-result"
    assert (
        captured["dataset_name"]
        == "incident-triage-golden-v1"
    )
    assert (
        captured["experiment_prefix"]
        == "incident-triage-baseline"
    )
    assert captured["max_concurrency"] == 1
    assert captured["error_handling"] == "log"

    metadata = captured["metadata"]

    assert metadata["agent_version"]
    assert metadata["prompt_version"]
    assert metadata["dataset_version"]
    assert metadata["environment"] == "local-fictional"

    assert len(captured["evaluators"]) == 5