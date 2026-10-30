# Security policy

## Supported versions

Only the latest release receives security fixes. The self-hosted Flatpak
repository delivers it automatically; the standalone bundle and native
packages need a manual update.

## Reporting a vulnerability

Please do not open a public issue. Report it privately through GitHub:
**Security** tab of this repository, then **Report a vulnerability**.

Include what you found, how to reproduce it, and the Rature version
(**About Rature** in the main menu, or `flatpak info io.github.vertours.Rature`).

## What to expect

Rature is maintained by one person. You will get an acknowledgement within
seven days. There is no committed delay for a fix; you will be kept
informed of progress, and credited in the release notes unless you prefer
otherwise.

## Scope

In scope: the application itself, how it stores your data (file
permissions, atomic writes, migrations), and the release pipeline (the
signed Flatpak repository, the bundle and the packaging files).

Out of scope: vulnerabilities in the GNOME runtime, GTK, libadwaita or
Python. Report those to their upstream projects.
