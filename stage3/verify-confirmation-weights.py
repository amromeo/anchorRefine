"""Verify the accepted weights and archived development receipt before confirmation."""
from hashlib import sha256
import json
from pathlib import Path

def digest(path):
    return sha256(path.read_bytes()).hexdigest()

archive = Path("results/stage3-development-45413443007")
selected = json.loads(Path("results/stage3-development/selected-weights.json").read_text())
receipt = json.loads((archive/"receipt.json").read_text())
dev = selected["development"]
if not (dev["run_id"] == 45413443007 and
        dev["source_commit"] == "2feb4868b1b8fe64ce3c956a038bc3e60313c1b9" and
        dev["datasets"] == receipt["datasets"] == 3744 and
        receipt["phase"] == selected["phase"] == "development" and receipt["passed"] is True and
        selected["primary_weight_w"] == receipt["chosen_w"] == 1 and
        selected["postfit_weight_t"] == receipt["chosen_t"] == .25 and
        dev["source_manifest_sha256"] == digest(Path("stage3/SHA256SUMS")) ==
        digest(archive/"source-manifest.sha256") == "5db4755face4cb67db6e4ac35cd33c859859fbb79cbd4f4d833263a0ee5a8251"):
    raise SystemExit("The accepted Stage 3 development release or weights differ.")
for name in ("receipt.json", "selection.csv", "evidence/audit.json"):
    if digest(archive/name) != selected["archive_sha256"][name]:
        raise SystemExit(f"Development evidence digest differs for {name}")
if digest(archive/"selection.csv") != receipt["selection_sha256"] or digest(archive/"evidence/audit.json") != receipt["audit_sha256"]:
    raise SystemExit("Development receipt does not match the selection and audit.")
