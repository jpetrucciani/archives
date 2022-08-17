{ jacobi ? import
    (
      fetchTarball {
        name = "jpetrucciani-2022-08-17";
        url = "https://github.com/jpetrucciani/nix/archive/93ad4046a5fe9924282af9c56dc88012d8b5315e.tar.gz";
        sha256 = "1ps5d55qvmh66n3xlmm1avsczl6xz82xic2n3vqrd1aj31kzdkm3";
      }
    )
    {
      overlays = [ (import ./overlays.nix) ];
    }
}:
let
  inherit (jacobi.hax) ifIsLinux ifIsDarwin;

  name = "archives";
  tools = with jacobi; {
    cli = [
      jq
      nixpkgs-fmt
    ];
    python = [
      (python310.withPackages (p: with p; [
        click
        lizard
        radon
        typed-ast

        # dev
        pytest
        pytest-cov
        setuptools
        tox
      ]))
    ];
    scripts = [
      (writeShellScriptBin "test_actions" ''
        ${jacobi.act}/bin/act --artifact-server-path ./.cache/ -r --rm
      '')
    ];
  };

  env = jacobi.enviro {
    inherit name tools;
  };
in
env
