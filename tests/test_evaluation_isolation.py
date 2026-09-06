import importlib

from src.mcp_client import create_mcp_client
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
def test_mcp_servers_receive_data_file_overrides(
    tmp_path,
    monkeypatch,
):
    service_now_file = (
        tmp_path / "incidents.json"
    )
    jira_file = tmp_path / "jira_issues.json"
    outlook_file = (
        tmp_path / "notifications.json"
    )

    monkeypatch.setenv(
        "SERVICENOW_DATA_FILE",
        str(service_now_file),
    )
    monkeypatch.setenv(
        "JIRA_DATA_FILE",
        str(jira_file),
    )
    monkeypatch.setenv(
        "OUTLOOK_DATA_FILE",
        str(outlook_file),
    )

    client = create_mcp_client()

    assert client.connections[
        "servicenow"
    ]["env"]["SERVICENOW_DATA_FILE"] == str(
        service_now_file
    )

    assert client.connections[
        "jira"
    ]["env"]["JIRA_DATA_FILE"] == str(
        jira_file
    )

    assert client.connections[
        "outlook"
    ]["env"]["OUTLOOK_DATA_FILE"] == str(
        outlook_file
    )