let
  pynixifyOverlay =
    final: prev: {
      python310 = prev.python310.override { inherit packageOverrides; };
      python311 = prev.python311.override { inherit packageOverrides; };
    };
  packageOverrides = final: prev: with final;
    let
      inherit (stdenv) isLinux isDarwin isAarch64;
      isM1 = isDarwin && isAarch64;
    in
    {
      lizard = buildPythonPackage rec {
        pname = "lizard";
        version = "1.17.10";

        src = fetchPypi {
          inherit pname version;
          sha256 = "1p2s0wx1l75dsljiyvars7xlljzs1mipm8jaby5y4jvjck6qmmv2";
        };

        pythonImportsCheck = [
          "lizard"
        ];

        doCheck = false;

        meta = with lib; {
          description =
            "A code analyzer without caring the C/C++ header files. It works with Java, C/C++, JavaScript, Python, Ruby, Swift, Objective C. Metrics includes cyclomatic complexity number etc.";
          homepage = "http://www.lizard.ws";
        };
      };

      radon = buildPythonPackage rec {
        pname = "radon";
        version = "5.1.0";

        src = fetchPypi {
          inherit pname version;
          sha256 = "1vmf56zsf3paa1jadjcjghiv2kxwiismyayq42ggnqpqwm98f7fb";
        };

        propagatedBuildInputs = [ mando colorama future ];

        pythonImportsCheck = [
          "radon"
        ];

        doCheck = false;

        meta = with lib; {
          description = "Code Metrics in Python";
          homepage = "https://radon.readthedocs.org/";
        };
      };

      mando = buildPythonPackage rec {
        pname = "mando";
        version = "0.6.4";

        src = fetchPypi {
          inherit pname version;
          sha256 = "0q6rl085q1hw1wic52pqfndr0x3nirbxnhqj9akdm5zhq2fv3zkr";
        };

        propagatedBuildInputs = [ six ];

        pythonImportsCheck = [
          "mando"
        ];

        doCheck = false;

        meta = with lib; {
          description = "Create Python CLI apps with little to no effort at all!";
          homepage = "https://mando.readthedocs.org/";
        };
      };
    };
in
pynixifyOverlay
