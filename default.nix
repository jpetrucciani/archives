let
  mach-nix = import (
    fetchTarball {
      name = "mach-nix-3.3.0";
      url = "https://github.com/DavHau/mach-nix/archive/3.3.0.tar.gz";
      sha256 = "105d6b6kgvn8kll639vx5adh5hp4gjcl4bs9rjzzyqz7367wbxj6";
    }
  ) { python = "python39"; };
in
mach-nix.mkPythonShell {
  requirements = ''
    ${builtins.readFile ./requirements.txt}
    ${builtins.readFile ./requirements-dev.txt}
  '';
}
