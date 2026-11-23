# Third-Party Notices

This repository contains an independently written MobileClaw automation
implementation. Account credentials are supplied at runtime and are not
included in the repository.

## Protocol Evidence

### MobileClaw

- Source: `lyimoexiao/opencode-mobileclaw-auth`
- Fixed commit reviewed:
  `06550f02a3105a292d8dd4e5bdf9d6d6f49064d9`
- License status: no SPDX license was present at the reviewed commit.
- Use: protocol evidence only.
- Local implementation: independently written; no source code from the
  upstream repository was copied or vendored into this project.

The fixed commit is recorded so that the reviewed request paths, request
bodies, response-field semantics, and activity identifiers remain auditable.
It does not grant a license to the upstream repository. Anyone redistributing
or extending this project must independently review the applicable terms of
the upstream project and the MobileClaw service.

## Runtime Dependencies

- `requests` is installed from PyPI under its own license.

## Project License

The local implementation is released under the MIT License reproduced in
[`LICENSE`](LICENSE).
