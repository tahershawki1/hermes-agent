# Owner-controlled Hermes Agent source

This repository is the runtime source for Hermes Mobile. It retains the complete
upstream Git history as a fork and keeps `main` as the stable integration branch.
`upstream-sync` is reserved for comparisons and pull requests from
`NousResearch/hermes-agent`; it is never used by phone installation scripts.

Mobile-specific changes that have already landed upstream are not re-applied by
the app. The app keeps its patch files only as a migration guard for older
checkouts, and the installer switches existing checkouts to this repository.
