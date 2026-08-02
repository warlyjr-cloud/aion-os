{
  description = "AION OS - safe, verifiable evolution engine for NixOS";

  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-25.11";

  outputs = {
    self,
    nixpkgs,
  }: let
    supportedSystems = ["x86_64-linux" "aarch64-linux"];
    forAllSystems = nixpkgs.lib.genAttrs supportedSystems;
    pkgsFor = system: import nixpkgs {inherit system;};
  in {
    nixosModules = {
      aion = import ./nix/modules/aion.nix;
      default = self.nixosModules.aion;
    };

    nixosConfigurations = {
      aion-lab = nixpkgs.lib.nixosSystem {
        system = "x86_64-linux";
        specialArgs.aionPackage = self.packages.x86_64-linux.default;
        modules = [./nix/hosts/aion-lab.nix];
      };

      aion-iso = nixpkgs.lib.nixosSystem {
        system = "x86_64-linux";
        specialArgs.aionPackage = self.packages.x86_64-linux.default;
        modules = [./nix/iso/default.nix];
      };
    };

    packages = forAllSystems (
      system: let
        pkgs = pkgsFor system;
      in
        {
          aion = pkgs.callPackage ./nix/package.nix {};
          default = self.packages.${system}.aion;
        }
        // nixpkgs.lib.optionalAttrs (system == "x86_64-linux") {
          aion-lab-vm = self.nixosConfigurations.aion-lab.config.system.build.vm;
          aion-iso = self.nixosConfigurations.aion-iso.config.system.build.isoImage;
        }
    );

    checks = forAllSystems (
      system: let
        pkgs = pkgsFor system;
      in
        {
          package = self.packages.${system}.aion;
        }
        // nixpkgs.lib.optionalAttrs (system == "x86_64-linux") {
          aiond-vm = import ./nix/tests {
            inherit pkgs;
            aionModule = self.nixosModules.aion;
            aionPackage = self.packages.${system}.aion;
          };
        }
    );

    devShells = forAllSystems (
      system: let
        pkgs = pkgsFor system;
        python = pkgs.python312.withPackages (pythonPackages:
          with pythonPackages; [
            hatchling
            hypothesis
            pydantic
            pytest
            pytest-cov
            typer
          ]);
      in {
        default = pkgs.mkShellNoCC {
          packages = with pkgs; [
            alejandra
            deadnix
            git
            gitleaks
            grype
            osv-scanner
            python
            pyright
            ruff
            semgrep
            statix
            syft
            uv
          ];
          AION_RUNTIME_MODE = "simulation";
          AION_ALLOW_HOST_MUTATION = "0";
        };
      }
    );

    formatter = forAllSystems (system: (pkgsFor system).alejandra);
  };
}
