# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 VertOurs

project(
  'rature',
  version: '0.5.0',
  license: 'GPL-3.0-or-later',
  meson_version: '>= 1.9',
)

i18n = import('i18n')
gnome = import('gnome')
python = import('python')

# The launcher targets whichever interpreter carries PyGObject. Under the
# GNOME runtime and in CI that is plain `python3`; on a host with a split
# between the tooling venv and the system interpreter, point it at the one
# that can `import gi` with `-Dpython=/usr/bin/python3`.
py = python.find_installation(get_option('python'))

prefix = get_option('prefix')
bindir = prefix / get_option('bindir')
datadir = prefix / get_option('datadir')
pkgdatadir = datadir / meson.project_name()
localedir = prefix / get_option('localedir')

subdir('src')
subdir('data')
subdir('po')

# `meson test` runs the pytest suite. pytest is a development dependency and
# is resolved from PATH, so run this from the activated project venv.
pytest = find_program('pytest', required: false)
if pytest.found()
  test(
    'pytest',
    pytest,
    args: ['-q'],
    workdir: meson.project_source_root(),
    timeout: 120,
  )
else
  message('pytest not found, the "pytest" test is skipped')
endif

gnome.post_install(
  gtk_update_icon_cache: true,
  update_desktop_database: true,
  glib_compile_schemas: true,
)