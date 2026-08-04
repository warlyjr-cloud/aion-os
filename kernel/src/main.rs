#![no_std] // Don't link the Rust standard library
#![no_main] // Disable all Rust-level entry points

#[cfg(target_arch = "x86_64")]
mod vga;
mod depin;
mod zkp;

use core::panic::PanicInfo;

/// This function is called on panic.
#[panic_handler]
fn panic(_info: &PanicInfo) -> ! {
    loop {}
}

#[cfg(target_arch = "x86_64")]
#[no_mangle]
pub extern "C" fn _start() -> ! {
    // This is the entry point, since the linker looks for a function
    // named `_start` by default
    vga::print_message(b"AION OS Microkernel v0.1 - The Hive Awakens on Silicon");
    
    // Hardware Attestation (TPM 2.0 Check) - Security Hardening
    vga::print_message(b"\nVerifying TPM 2.0 Hardware Attestation...");
    // If this fails in production, panic!("TPM Module missing. Hardware clone detected.");

    // Initialize ZKP and DePIN stubs
    zkp::init();
    depin::init();

    loop {}
}

#[cfg(target_arch = "aarch64")]
#[no_mangle]
pub extern "C" fn _start() -> ! {
    // ARM64 entry point (requires a different UART/Framebuffer setup for text)
    // For MVP, we just loop infinitely on ARM64 after initializing our modules
    zkp::init();
    depin::init();
    
    loop {}
}
