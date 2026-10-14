# Input handling and evidence boundaries

Use this tool on caller-controlled copies of saved regular files. It opens no
network connections and has no privileged or hardware API. It does not discover
files from report text. The CLI bounds reads, validates selections before opening
companions, and hashes the exact bytes then parsed. It never prints input paths,
names, report values, inventory addresses, or settings bytes in result summaries.

An explicitly selected symlink can resolve to a regular file. This CLI is not a
sandbox against an adversary changing the input directory concurrently. Copy
inputs into a directory you control; do not use it as a privileged ingestion
service. Library callers are responsible for limiting input acquisition before
passing in-memory bytes. The parser's caps bound work after acquisition.

Hash declarations live in unauthenticated input. An attacker can replace a file
and its digest together. Structure checks cannot prove provenance, atomicity,
freshness, successful save finalization, real hardware state, or firmware safety.

No security contact or hosted issue tracker exists for this local candidate.
Before publication, establish a private reporting contact. Never attach real
device reports, private paths, identifiers, settings dumps, binaries, or captured
firmware to public issues; supply a minimal synthetic reproducer instead.
