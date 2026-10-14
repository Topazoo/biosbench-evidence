# Publication status and protection proposal

Public repository: https://github.com/Topazoo/biosbench-evidence

Peter Swanson authorized public publication and MIT licensing on 2026-10-14.
The reviewed history was pushed using his existing authenticated GitHub route.
No credentials, grants, global Git/auth settings, or engineering files changed.

## Hosted validation

The first run passed on Linux but Windows could not install Python 3.12.14.
The corrected workflow pins Python 3.12.10, available on both platforms, and
runs unit tests, the explicit file/privacy/fixture checks, and archive creation.
See the Actions tab for the latest commit-specific result. Local tests use
Python 3.12.14; they are distinct from hosted results.

## Inspected settings and proposed changes

Inspection on 2026-10-14 found public visibility, default branch main, no branch
protection or rulesets, and one collaborator: the owner with admin access.
Secret scanning and push protection are already enabled. Workflow default token
permissions are read-only and workflow approval of pull requests is disabled.
Private vulnerability reporting is disabled. All three merge methods are enabled.

No protection or security setting has been changed. The following concrete
proposal requires separate action-time owner approval:

- Protect main, including administrators, with no force pushes or branch deletion.
- Require pull requests and resolved review conversations.
- Require the GitHub Actions checks named test (ubuntu-latest) and
  test (windows-latest), with the branch up to date before merging.
- Require linear history; allow squash merges only, disabling merge commits and
  rebase merges.
- Use zero required approving reviews while the owner is the sole collaborator:
  the owner cannot approve their own pull request. Require one approval and
  dismiss stale approvals once a second reviewer is explicitly appointed.
- Enable private vulnerability reporting to provide a private security channel.
- Keep existing secret scanning, push protection, read-only workflow permissions,
  and prohibition on workflow pull-request approval unchanged.

The exact settings and check identities must be re-read at application time.
This proposal does not authorize applying them or adding collaborators.

## Evidence limits

The first release intentionally supports a narrower portable API than the
engineering application. Flash-survey payload structure and board extensions
remain unsupported. No firmware-safety, full semantic-compatibility, or physical
validation claim is made. Private audit and approval records remain outside the
repository and archive. Ongoing engineering workspaces remain out of scope.
