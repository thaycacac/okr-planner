from tests.api_support import ApiHarness


def test_quarter_crud_and_duplicates(api: ApiHarness) -> None:
    created = api.client.post("/quarters", json={"year": 2026, "number": 4})
    assert created.status_code == 201
    quarter = created.json()
    assert quarter["start_date"] == "2026-10-01"
    assert quarter["end_date"] == "2026-12-31"
    assert quarter["objectives"] == []
    assert quarter["latest_plan_run_id"] is None

    duplicate = api.client.post("/quarters", json={"year": 2026, "number": 4})
    assert duplicate.status_code == 409
    assert duplicate.json()["detail"]["code"] == "quarter_exists"

    assert api.client.post("/quarters", json={"year": 2026, "number": 5}).status_code == 422
    assert [q["id"] for q in api.client.get("/quarters").json()] == [quarter["id"]]

    assert api.client.delete(f"/quarters/{quarter['id']}").status_code == 204
    missing = api.client.get(f"/quarters/{quarter['id']}")
    assert missing.status_code == 404
    assert missing.json()["detail"]["code"] == "not_found"


def test_objective_and_key_result_lifecycle(api: ApiHarness) -> None:
    quarter_id = api.client.post("/quarters", json={"year": 2026, "number": 4}).json()["id"]
    objective = api.client.post(
        f"/quarters/{quarter_id}/objectives",
        json={
            "title": "  Ship the onboarding revamp  ",
            "key_results": [
                {"text": "Activation rate", "kind": "numeric", "baseline": 20, "target": 35},
                {"text": "Publish help center", "kind": "milestone", "due_date": "2026-11-30"},
            ],
        },
    ).json()
    assert objective["title"] == "Ship the onboarding revamp"
    assert objective["priority"] == "medium"
    assert objective["position"] == 0
    assert [kr["position"] for kr in objective["key_results"]] == [0, 1]
    assert objective["key_results"][0]["unit"] is None
    assert objective["key_results"][1]["due_date"] == "2026-11-30"

    second = api.client.post(
        f"/quarters/{quarter_id}/objectives", json={"title": "Second", "priority": "high"}
    ).json()
    assert second["position"] == 1

    patched = api.client.patch(
        f"/objectives/{objective['id']}", json={"priority": "low", "position": 5}
    ).json()
    assert (patched["priority"], patched["position"]) == ("low", 5)

    kr = api.client.post(
        f"/objectives/{objective['id']}/key-results", json={"text": "NPS above 40"}
    ).json()
    assert kr["position"] == 2
    assert kr["kind"] == "other"

    updated = api.client.patch(
        f"/key-results/{kr['id']}", json={"kind": "numeric", "target": 40, "unit": "pts"}
    ).json()
    assert (updated["kind"], updated["target"], updated["unit"]) == ("numeric", 40, "pts")
    cleared = api.client.patch(f"/key-results/{kr['id']}", json={"unit": None}).json()
    assert cleared["unit"] is None
    assert api.client.patch(f"/key-results/{kr['id']}", json={"text": None}).status_code == 422
    assert api.client.patch(f"/key-results/{kr['id']}", json={"bogus": 1}).status_code == 422

    assert api.client.delete(f"/key-results/{kr['id']}").status_code == 204
    assert api.client.get(f"/key-results/{kr['id']}").status_code == 404

    detail = api.client.get(f"/quarters/{quarter_id}").json()
    assert [o["id"] for o in detail["objectives"]] == [second["id"], objective["id"]]
    assert detail["key_result_count"] == 2

    assert api.client.delete(f"/objectives/{objective['id']}").status_code == 204
    assert api.client.get(f"/quarters/{quarter_id}").json()["key_result_count"] == 0


def test_missing_parents_are_404(api: ApiHarness) -> None:
    assert api.client.post("/quarters/9/objectives", json={"title": "x"}).status_code == 404
    assert api.client.post("/objectives/9/key-results", json={"text": "x"}).status_code == 404
    assert api.client.get("/quarters/9/tasks").status_code == 404
    assert api.client.get("/quarters/9/schedule").status_code == 404
    assert api.client.get("/tasks/9").status_code == 404


def test_schedule_is_404_until_a_plan_succeeds(api: ApiHarness) -> None:
    quarter_id = api.client.post("/quarters", json={"year": 2026, "number": 4}).json()["id"]
    response = api.client.get(f"/quarters/{quarter_id}/schedule")
    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "schedule_not_found"
