import importlib

import servers.jira_server as jira
import servers.outlook_server as outlook
import servers.servicenow_server as servicenow


def assert_data_file_override(
    module,
    monkeypatch,
    variable,
    target,
):
    monkeypatch.setenv(variable, str(target))

    reloaded = importlib.reload(module)

    assert reloaded.DATA_FILE == target

    monkeypatch.delenv(variable)
    importlib.reload(module)


def test_servicenow_path_override(
    tmp_path,
    monkeypatch,
):
    assert_data_file_override(
        servicenow,
        monkeypatch,
        "SERVICENOW_DATA_FILE",
        tmp_path / "incidents.json",
    )


def test_jira_path_override(
    tmp_path,
    monkeypatch,
):
    assert_data_file_override(
        jira,
        monkeypatch,
        "JIRA_DATA_FILE",
        tmp_path / "jira_issues.json",
    )


def test_outlook_path_override(
    tmp_path,
    monkeypatch,
):
    assert_data_file_override(
        outlook,
        monkeypatch,
        "OUTLOOK_DATA_FILE",
        tmp_path / "notifications.json",
    )
