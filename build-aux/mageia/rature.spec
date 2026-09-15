# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 VertOurs

Name:           rature
Version:        1.0.0
Release:        1
Summary:        Your day, one line at a time: a daily-list desktop app for GNOME

License:        GPL-3.0-or-later
URL:            https://github.com/VertOurs/Rature
Source0:        https://github.com/VertOurs/Rature/archive/refs/tags/v%{version}.tar.gz#/rature-%{version}.tar.gz

BuildArch:      noarch

BuildRequires:  meson
BuildRequires:  ninja
BuildRequires:  gettext
BuildRequires:  lib64python3-devel
BuildRequires:  python3-gobject-devel
BuildRequires:  lib64gtk4.0-devel
BuildRequires:  lib64adwaita-devel
BuildRequires:  lib64glib2.0-devel
BuildRequires:  desktop-file-utils
BuildRequires:  appstream
BuildRequires:  python3-pytest

# glib2 is not required explicitly: gtk4.0 and libadwaita already pull it
# in, and its runtime package is named by soname (lib64glib2.0_0), too
# unstable to hardcode here.
Requires:       python3-gobject
Requires:       gobject-introspection
Requires:       gtk4.0
Requires:       libadwaita

%description
Rature reproduces a daily-list method: dictate tasks one at a time, strike
them off through the day, with no planning and no categories. It has no
persistent history beyond a read-only archive: yesterday's list is closed,
not carried forward.

%prep
%autosetup -n Rature-%{version}

%build
%meson
%meson_build

%check
%meson_test

%install
%meson_install
%find_lang %{name}

%files -f %{name}.lang
%license LICENSE
%doc README.md
%{_bindir}/rature
%{_datadir}/applications/io.github.vertours.Rature.desktop
%{_datadir}/metainfo/io.github.vertours.Rature.metainfo.xml
%{_datadir}/glib-2.0/schemas/io.github.vertours.Rature.gschema.xml
%{_datadir}/icons/hicolor/scalable/apps/io.github.vertours.Rature.svg
%{_datadir}/rature/

%changelog
* Tue Sep 15 2026 VertOurs <vertours.dev@gmail.com> - 1.0.0-1
- Initial Mageia packaging, mirroring the AUR PKGBUILD and COPR spec
  (build-aux/aur/, build-aux/copr/).
