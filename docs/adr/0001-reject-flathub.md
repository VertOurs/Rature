# ADR 0001: reject Flathub, self-hosted Flatpak repository

- **Date**: 2026-08-24
- **Status**: accepted

## Context

Flathub was the intended distribution channel, for its visibility and its
automatic updates. Flathub's policy, tightened on 29 May 2026, forbids any
AI-generated or AI-assisted content, in the application as in the
submission: manifest, metadata, patches, build scripts, pull request text.
It is not retroactive and makes exceptions for mature, well-maintained
projects, which does not describe a project that is just starting. GNOME
Circle suspended new submissions on 30 May 2026.

The project is developed with the assistance of an agent. Three paths were
open: write all the code without assistance, give up on these two
channels, or give up on publishing.

## Decision

Neither Flathub nor GNOME Circle. Distribution goes through:

1. A static, self-hosted Flatpak repository on GitHub Pages, the main
   channel
2. A `.flatpak` bundle attached to each release, to try without committing
3. AUR and COPR, native packages with a low maintenance cost

## Consequences

- Automatic updates are kept, once the repository is added
- Visibility in GNOME Software is lost
- A GPG signing key becomes critical: without it, no update can ever be
  published to the repository again
- Flathub's quality requirements are kept on purpose: they served
  maintainability as much as compliance
