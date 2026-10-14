# Remaining publication prerequisites

1. Establish the actual authors/rights holders of each source-derived component
   in PROVENANCE.md, including any copied third-party portions. Obtain explicit
   redistribution and MIT licensing authorization. Complete the copyright line
   and replace the provisional LICENSE notice; do not publish it as MIT today.
2. Review the exact allowlisted source archive for privacy and license clearance.
   The private audit directory is outside the repository and must stay private.
   Confirm that excluded device evidence, board-specific analysis, binaries,
   images, offsets, and private identifiers have not been reintroduced.
3. Decide whether this deliberately narrower portable API is an acceptable first
   release. Flash-survey semantics and board extensions are not validated. A full
   compatibility release requires separately reviewed generic adapters and tests.
4. Execute the committed CI matrix on Linux and Windows using Python 3.12.14.
   Local Windows tests do not establish Linux runtime validation. Review archive
   reproducibility and any additional release-specific checks.
5. Choose the repository account/name, establish a security contact, and get
   explicit authorization to publish that reviewed version. No account access,
   remote repository creation, uploads, or GitHub publication was authorized here.

These are release gates, not requests to change or pause ongoing engineering.
The current local artifact is intended for code review and licensing decisions.
