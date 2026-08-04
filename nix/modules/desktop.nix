{ config, lib, pkgs, ... }:

let
  cfg = config.services.aion.desktop;
in {
  options.services.aion.desktop = {
    enable = lib.mkEnableOption "AION Generative Desktop Environment (Hyprland)";
  };

  config = lib.mkIf cfg.enable {
    programs.hyprland.enable = true;
    
    environment.systemPackages = with pkgs; [
      waybar
      kitty
      rofi-wayland
      swaybg
      dunst
    ];
    
    services.displayManager = {
      sddm.enable = true;
      sddm.wayland.enable = true;
      autoLogin.enable = true;
      autoLogin.user = "aion-lab";
    };
    
    # Fonts
    fonts.packages = with pkgs; [
      nerd-fonts.fira-code
      nerd-fonts.jetbrains-mono
    ];
  };
}
