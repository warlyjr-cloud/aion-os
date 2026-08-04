// VGA buffer address is always 0xb8000 on x86
const VGA_BUFFER: *mut u8 = 0xb8000 as *mut u8;

pub fn print_message(message: &[u8]) {
    let mut offset = 0;
    
    for (i, &byte) in message.iter().enumerate() {
        unsafe {
            // Write byte and color code (0x0A is light green on black)
            *VGA_BUFFER.offset(offset as isize) = byte;
            *VGA_BUFFER.offset((offset + 1) as isize) = 0x0A;
        }
        offset += 2;
    }
}
