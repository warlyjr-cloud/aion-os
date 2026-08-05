#include "sha256.h"
#include <cstring>
#include <iomanip>
#include <sstream>
#include <ostream>
#include <iostream>

namespace aion {
namespace crypto {

#define ROTR(x, n) (((x) >> (n)) | ((x) << (32 - (n))))

static const uint32_t K[64] = {
    0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5, 0x3956c25b, 0x59f111f1, 0x923f82a4, 0xab1c5ed5,
    0xd807aa98, 0x12835b01, 0x243185be, 0x550c7dc3, 0x72be5d74, 0x80deb1fe, 0x9bdc06a7, 0xc19bf174,
    0xe49b69c1, 0xefbe4786, 0x0fc19dc6, 0x240ca1cc, 0x2de92c6f, 0x4a7484aa, 0x5cb0a9dc, 0x76f988da,
    0x983e5152, 0xa831c66d, 0xb00327c8, 0xbf597fc7, 0xc6e00bf3, 0xd5a79147, 0x06ca6351, 0x14292967,
    0x27b70a85, 0x2e1b2138, 0x4d2c6dfc, 0x53380d13, 0x650a7354, 0x766a0abb, 0x81c2c92e, 0x92722c85,
    0xa2bfe8a1, 0xa81a664b, 0xc24b8b70, 0xc76c51a3, 0xd192e819, 0xd6990624, 0xf40e3585, 0x106aa070,
    0x19a4c116, 0x1e376c08, 0x2748774c, 0x34b0bcb5, 0x391c0cb3, 0x4ed8aa4a, 0x5b9cca4f, 0x682e6ff3,
    0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208, 0x90befffa, 0xa4506ceb, 0xbef9a3f7, 0xc67178f2
};

SHA256::SHA256() {
    init();
}

void SHA256::init() {
    m_state[0] = 0x6a09e667;
    m_state[1] = 0xbb67ae85;
    m_state[2] = 0x3c6ef372;
    m_state[3] = 0xa54ff53a;
    m_state[4] = 0x510e527f;
    m_state[5] = 0x9b05688c;
    m_state[6] = 0x1f83d9ab;
    m_state[7] = 0x5be0cd19;
    m_count = 0;
    std::memset(m_buffer, 0, BLOCK_SIZE);
}

void SHA256::transform(const uint8_t block[64]) {
    uint32_t W[64];
    for (int i = 0; i < 16; ++i) {
        W[i] = (static_cast<uint32_t>(block[i * 4]) << 24) |
               (static_cast<uint32_t>(block[i * 4 + 1]) << 16) |
               (static_cast<uint32_t>(block[i * 4 + 2]) << 8) |
               (static_cast<uint32_t>(block[i * 4 + 3]));
    }
    for (int i = 16; i < 64; ++i) {
        uint32_t s0 = ROTR(W[i - 15], 7) ^ ROTR(W[i - 15], 18) ^ (W[i - 15] >> 3);
        uint32_t s1 = ROTR(W[i - 2], 17) ^ ROTR(W[i - 2], 19) ^ (W[i - 2] >> 10);
        W[i] = W[i - 16] + s0 + W[i - 7] + s1;
    }

    uint32_t a = m_state[0], b = m_state[1], c = m_state[2], d = m_state[3];
    uint32_t e = m_state[4], f = m_state[5], g = m_state[6], h = m_state[7];

    for (int i = 0; i < 64; ++i) {
        uint32_t S1 = ROTR(e, 6) ^ ROTR(e, 11) ^ ROTR(e, 25);
        uint32_t ch = (e & f) ^ ((~e) & g);
        uint32_t temp1 = h + S1 + ch + K[i] + W[i];
        uint32_t S0 = ROTR(a, 2) ^ ROTR(a, 13) ^ ROTR(a, 22);
        uint32_t maj = (a & b) ^ (a & c) ^ (b & c);
        uint32_t temp2 = S0 + maj;

        h = g;
        g = f;
        f = e;
        e = d + temp1;
        d = c;
        c = b;
        b = a;
        a = temp1 + temp2;
    }

    m_state[0] += a; m_state[1] += b; m_state[2] += c; m_state[3] += d;
    m_state[4] += e; m_state[5] += f; m_state[6] += g; m_state[7] += h;
}

void SHA256::update(const uint8_t* data, size_t len) {
    size_t buffer_bytes = static_cast<size_t>((m_count >> 3) & 0x3F);
    m_count += static_cast<uint64_t>(len) << 3;

    size_t part_len = 64 - buffer_bytes;
    size_t i = 0;

    if (len >= part_len) {
        std::memcpy(&m_buffer[buffer_bytes], data, part_len);
        transform(m_buffer);
        for (i = part_len; i + 63 < len; i += 64) {
            transform(&data[i]);
        }
        buffer_bytes = 0;
    }

    if (i < len) {
        std::memcpy(&m_buffer[buffer_bytes], &data[i], len - i);
    }
}

void SHA256::final(uint8_t digest[32]) {
    uint8_t final_count[8];
    for (int i = 0; i < 8; ++i) {
        final_count[i] = static_cast<uint8_t>((m_count >> ((7 - i) * 8)) & 0xFF);
    }

    size_t buffer_bytes = static_cast<size_t>((m_count >> 3) & 0x3F);
    size_t pad_len = (buffer_bytes < 56) ? (56 - buffer_bytes) : (120 - buffer_bytes);

    static const uint8_t padding[64] = {
        0x80, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0
    };

    update(padding, pad_len);
    update(final_count, 8);

    for (int i = 0; i < 8; ++i) {
        digest[i * 4]     = static_cast<uint8_t>((m_state[i] >> 24) & 0xFF);
        digest[i * 4 + 1] = static_cast<uint8_t>((m_state[i] >> 16) & 0xFF);
        digest[i * 4 + 2] = static_cast<uint8_t>((m_state[i] >> 8) & 0xFF);
        digest[i * 4 + 3] = static_cast<uint8_t>(m_state[i] & 0xFF);
    }
}

void SHA256::hash(const uint8_t* data, size_t len, uint8_t digest[32]) {
    SHA256 ctx;
    ctx.update(data, len);
    ctx.final(digest);
}

std::array<uint8_t, 32> SHA256::hash(const uint8_t* data, size_t len) {
    std::array<uint8_t, 32> digest;
    hash(data, len, digest.data());
    return digest;
}

std::string SHA256::bytesToHex(const uint8_t* data, size_t len) {
    std::ostringstream ss;
    for (size_t i = 0; i < len; ++i) {
        ss << std::hex << std::setw(2) << std::setfill('0') << static_cast<unsigned int>(data[i]);
    }
    return ss.str();
}

std::string SHA256::hashToHex(const uint8_t* data, size_t len) {
    uint8_t digest[32];
    hash(data, len, digest);
    return bytesToHex(digest, 32);
}

} // namespace crypto
} // namespace aion
