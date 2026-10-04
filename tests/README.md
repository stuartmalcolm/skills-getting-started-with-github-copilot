# Backend API Test Cases

The API tests are in `test_app.py` and use the Arrange-Act-Assert (AAA) pattern. Each test restores the in-memory activity data after it runs, keeping cases independent.

| Case | Arrange / Act | Expected result |
| --- | --- | --- |
| Frontend redirect | Request `GET /` without following redirects | `307` redirect to `/static/index.html` |
| Activity listing | Request `GET /activities` | `200` and activities include participant lists |
| Signup success and encoded name | Sign up using an encoded activity name containing spaces | `200`; participant is added |
| Duplicate signup | Sign up an already-registered email | `400`; participant list is unchanged |
| Unknown activity signup | Sign up for a nonexistent activity | `404`; no activity state changes |
| Signup at capacity boundary | Try signup one spot below, at, and above capacity | Last open spot succeeds; at/over capacity returns `409` without mutation |
| Signup email validation | Omit email or provide blank/malformed email | `422`; participant list is unchanged |
| Unregister success | Remove a registered email | `200`; participant is removed |
| Repeated unregister | Remove the same email again | `404`; participant remains absent |
| Unregister absent participant | Remove an email not in the activity | `404`; participant list is unchanged |
| Unknown activity unregister | Unregister from a nonexistent activity | `404`; no activity state changes |
| Unregister email validation | Omit email or provide blank/malformed email | `422`; participant list is unchanged |

Run the focused module and then the full suite from the project root:

```bash
python -m pytest -q tests/test_app.py
python -m pytest -q
```