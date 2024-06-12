{
  description = "lofi";

  inputs = {
    flake-utils.url = "github:numtide/flake-utils";
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        # see https://github.com/nix-community/poetry2nix/tree/master#api for more functions and examples.
        pkgs = nixpkgs.legacyPackages.${system};
        # inherit (poetry2nix.lib.mkPoetry2Nix { inherit pkgs; }) mkPoetryApplication;
      in
      {
        packages = {
          # myapp = mkPoetryApplication { projectDir = self; };
          default = self.packages.${system};
        };

        devShells.default = pkgs.mkShell {
          inputsFrom = [ self.packages.${system}.default ];
          packages = [
            pkgs.poetry
            pkgs.python312
            # python312Packages.fastapi
            # python312Packages.uvicorn
            # python312Packages.flake8
            # python312Packages.black
            # python312Packages.isort
            # python312Packages.pyaudio
            pkgs.portaudio
          ];

          # shellHook = ''
          #   export OLD_PS1="$PS1"
          #   export PS1="nix-shell:lofi $PS1"
          # '';

          # # reset ps1
          # shellExitHook = ''
          #   export PS1="$OLD_PS1"
          # '';
        };
      });
}