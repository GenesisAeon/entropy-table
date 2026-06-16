# Release Guide

This package follows the GenesisAeon ecosystem release process.

## Versioning

We use [Semantic Versioning](https://semver.org/): `MAJOR.MINOR.PATCH`.

- **MAJOR** — breaking changes to the public API or Diamond Interface.
- **MINOR** — new features, backwards-compatible.
- **PATCH** — bug fixes, documentation, dependency bumps.

## Release types

| Tag pattern | Channel | Where it publishes |
|---|---|---|
| `vX.Y.Z` | Production | PyPI, GitHub Release, Zenodo (if integration enabled) |
| `vX.Y.Z-rc.N`, `-alpha.N`, `-beta.N` | Canary | TestPyPI, GitHub pre-release |

## How to cut a release

1. Ensure `CHANGELOG.md` has an entry for the new version under `## [X.Y.Z]`.
2. Ensure the working tree is clean — `setuptools_scm` derives the version
   from the git tag, so no manual version bump is needed.
3. Commit any remaining changes to `main`.
4. Tag: `git tag vX.Y.Z && git push origin vX.Y.Z`.
5. The `.github/workflows/release.yml` workflow builds, tests, and publishes
   automatically.
6. For production releases, if Zenodo–GitHub integration is enabled for this
   repo, a new Zenodo DOI version is minted automatically from the GitHub
   Release using `.zenodo.json` metadata.

## Dependency pins within the GenesisAeon ecosystem

Pin other `GenesisAeon/*` packages with `>=` lower bounds matching the minimum
version that provides the API this package relies on. Do not use exact-version
pins (`==`) for ecosystem dependencies.
