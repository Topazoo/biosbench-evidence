# Publication and repository protections

Public repository: https://github.com/Topazoo/biosbench-evidence

Source provenance and dependency boundaries are recorded in PROVENANCE.md.

## Repository protections applied on 2026-10-14

- Main requires pull requests and resolved review conversations.
- GitHub Actions checks test (ubuntu-latest) and test (windows-latest) are
  required, bound to app ID 15368, with the branch up to date.
- Administrator enforcement and linear history are enabled.
- Force pushes and branch deletion are prohibited.
- Zero approving reviews are required while the owner is the sole collaborator.
- Squash is the only enabled merge method.
- Private vulnerability reporting is enabled.
- Existing secret scanning and push protection remain enabled. Workflow token
  permissions remain read-only; workflow approval of pull requests stays disabled.

## Validation and limits

CI pins Python 3.12.10 on Linux and Windows, runs synthetic tests and repository
checks, and builds a deterministic source archive. See the Actions tab for
commit-specific results. The initial Python 3.12.14 Windows installation failure
was corrected by selecting the available 3.12.10 patch version.

Flash-survey payload structure and board extensions remain unsupported. HII/IFR
checks cover framing and selected declarations, not expression semantics.
No firmware-safety or physical validation claim is made. Ongoing engineering
workspaces remain out of scope.
