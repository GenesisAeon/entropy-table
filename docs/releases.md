# Releases

## Zenodo-ready dataset packs (PR20)
Generate a distributable archive containing the validated graph snapshot, graph health report, and bibliography:

```bash
python tools/release.py --version <vX.Y.Z>
```

Example:

```bash
python tools/release.py --version v1.0.0
```

Output archive location:

- `dist/packs/entropy-table-pack-<vX.Y.Z>.zip`

Archive contents:

- `bundle.json` (canonical graph snapshot)
- `atlas_health.md` (health & coverage report)
- `refs.yaml` (bibliography)
- `MANIFEST.txt` (version + timestamp + file summary)
- `README.md` and `MANIFEST.json` (snapshot metadata)

You can upload the resulting `.zip` directly to Zenodo for DOI minting.

## Legacy snapshot and freeze workflows

### Create a snapshot

```bash
python tools/release.py snapshot --out dist/snapshots
```

### Verify a snapshot

```bash
python tools/release.py verify --path dist/snapshots/<snapshot_id>
```

### Freeze guard

```bash
python tools/release.py freeze-init
python tools/release.py freeze-verify
python tools/release.py freeze-update --allow-stable-edits
```
