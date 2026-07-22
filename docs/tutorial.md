# Lore Step-by-Step Tutorial

Learn how to work with **Collections**, **Artifact Subtypes**, **Wiki-Link Auto-Extraction**, **Version Diffs**, **Rollbacks**, and the **Dynamic Skill Registry**.

---

## 1. Organizing Work with Collections

Collections provide nested, folder-like organization for artifacts with database-backed permission inheritance.

### Create a Root Collection
```bash
curl -s -X POST "http://127.0.0.1:8000/api/collections/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "Engineering"}'
```

### Create a Nested Sub-Collection
```bash
curl -s -X POST "http://127.0.0.1:8000/api/collections/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "Backend", "parent_id": "<ENGINEERING_COLLECTION_ID>"}'
```

---

## 2. Creating First-Class Artifacts

Lore supports four first-class artifact types: `skill`, `decision`, `document`, and `memory`.

### Create a Skill Artifact
```bash
curl -s -X POST "http://127.0.0.1:8000/api/artifacts/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "skill",
    "title": "Django Ninja Patterns",
    "collection_id": "<BACKEND_COLLECTION_ID>",
    "skill_md_content": "# Skill\nUse Ninja Routers and Pydantic schemas for API endpoints."
  }'
```

---

## 3. Automatic Wiki-Link Graph Relations (`[[Title]]`)

When creating text artifacts, any `[[Artifact Title]]` syntax automatically parses matching artifacts in the workspace and creates a directed `references` edge in the **Artifact Graph**.

### Create a Decision referencing the Skill
```bash
curl -s -X POST "http://127.0.0.1:8000/api/artifacts/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "decision",
    "title": "Adopt Django Ninja",
    "collection_id": "<BACKEND_COLLECTION_ID>",
    "decision_text": "We will use [[Django Ninja Patterns]] for all API endpoints.",
    "rationale": "Pydantic validation and high performance."
  }'
```

### Query Graph Relationships
```bash
curl -s "http://127.0.0.1:8000/api/artifacts/<DECISION_ID>/relationships" \
  -H "Authorization: Bearer $TOKEN"
```
* **Result**: Displays outgoing `references` edge from `Adopt Django Ninja` to `Django Ninja Patterns`.

---

## 4. Version History & Line Diffs

Every edit to an artifact generates an immutable `ArtifactVersion` with automated line-by-line diff generation.

### Upload a Document File (v1)
```bash
echo "# Deployment Rules\n\n1. Run migrations before restarting." > deploy-rules.md

curl -s -X POST "http://127.0.0.1:8000/api/artifacts/upload?collection_id=<BACKEND_COLLECTION_ID>" \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@deploy-rules.md"
```

### Overwrite Document File (v2)
```bash
echo "# Deployment Rules\n\n1. Run migrations before restarting.\n2. Set DEBUG=False in production." > deploy-rules.md

curl -s -X POST "http://127.0.0.1:8000/api/artifacts/upload?collection_id=<BACKEND_COLLECTION_ID>" \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@deploy-rules.md"
```

### Inspect Version History & Diffs
```bash
curl -s "http://127.0.0.1:8000/api/artifacts/<DOC_ID>/versions" \
  -H "Authorization: Bearer $TOKEN"
```
* **Result**: Returns line diff `+ 2. Set DEBUG=False in production.`.

---

## 5. Append-Only Version Rollback

Rollbacks restore historical content snapshots without losing audit history.

```bash
curl -s -X POST "http://127.0.0.1:8000/api/artifacts/<DOC_ID>/revert?target_version_number=1&commit_message=Reverting+unapproved+rule" \
  -H "Authorization: Bearer $TOKEN"
```
* **Result**: Version 3 is created matching Version 1 content in an append-only audit trail.

---

## 6. Dynamic Skill Registry

Agents fetch prompt skills dynamically using title lookups or full-text chunk RAG search:

```bash
curl -s "http://127.0.0.1:8000/api/artifacts/skills/Django%20Ninja%20Patterns" \
  -H "Authorization: Bearer $TOKEN"
```
* **Result**: Returns skill content and atomically increments `usage_count`.
