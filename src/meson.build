# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 VertOurs

# The package ships as application data under <datadir>/rature/rature and the
# launcher puts that directory on sys.path. This keeps the install working
# under any prefix, without depending on the interpreter's site-packages.
moduledir = pkgdatadir / 'rature'

conf = configuration_data()
conf.set('VERSION', meson.project_version())
conf.set('PKGDATADIR', pkgdatadir)
conf.set('LOCALEDIR', localedir)

configure_file(
  input: 'rature/config.py.in',
  output: 'config.py',
  configuration: conf,
  install: true,
  install_dir: moduledir,
)

install_subdir(
  'rature',
  install_dir: pkgdatadir,
  exclude_files: ['config.py.in'],
  exclude_directories: ['__pycache__', 'core/__pycache__', 'ui/__pycache__'],
)

configure_file(
  input: 'rature.in',
  output: 'rature',
  configuration: {
    'PYTHON': py.full_path(),
    'PKGDATADIR': pkgdatadir,
    'LOCALEDIR': localedir,
  },
  install: true,
  install_dir: bindir,
  install_mode: 'rwxr-xr-x',
)