# Release Snapshots

## Create a snapshot
Run:

```bash
python tools/release.py snapshot --out dist/snapshots
```

Optional explicit id:

```bash
python tools/release.py snapshot --id 20260226-120000Z --out dist/snapshots
```

Outputs are written to:

- `dist/snapshots/<snapshot_id>/bundle.json`
- `dist/snapshots/<snapshot_id>/README.md`
- `dist/snapshots/<snapshot_id>/MANIFEST.json`

## Verify a snapshot

```bash
python tools/release.py verify --path dist/snapshots/<snapshot_id>
```

Verification checks bundle hash integrity and reports schema-hash drift warnings against the current repository state.

## Freeze guard workflows
Initialize stable-content freeze baseline:

```bash
python tools/release.py freeze-init
```

Verify no stable entries changed unexpectedly:

```bash
python tools/release.py freeze-verify
# or: python tools/release.py freeze-check
```

Intentionally accept stable edits:

```bash
python tools/release.py freeze-update --allow-stable-edits
```

Freeze manifests are local workflow artifacts (`dist/freeze/freeze_manifest.json`) and should not be committed.

## Citation format
Use:

`Entropy Atlas Snapshot <snapshot_id>, bundle_sha256=<bundle_sha256>`

Both values are available in the snapshot `MANIFEST.json`.

## Optional DOI workflow
A snapshot directory can be uploaded to archival services (for example Zenodo) to mint a DOI. DOI automation is intentionally not implemented in this repository.
