{lib, ...}: {
  boot.readOnlyNixStore = true;
  documentation.enable = false;
  networking.useDHCP = lib.mkDefault true;
  nix.settings = {
    experimental-features = ["nix-command" "flakes"];
    sandbox = true;
  };
  security.sudo.enable = false;
  services.getty.helpLine = "AION Lab: simulation-only; host mutation and network services are disabled.";
}
