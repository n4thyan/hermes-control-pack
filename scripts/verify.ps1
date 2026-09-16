$ErrorActionPreference = "Stop"
py -m compileall -q src\hermes_control_pack
py -m unittest discover -s tests -v
hcp --version
