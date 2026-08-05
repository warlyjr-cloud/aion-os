#ifndef AION_SHA256_H
#define AION_SHA256_H

#include <cstdint>
#include <cstddef>
#include <string>
#include <array>

namespace aion {
namespace crypto {

class SHA256 {
public:
    static constexpr size_t DIGEST_SIZE = 32;
    static constexpr size_t BLOCK_SIZE = 64;

    SHA256();
    void init();
    void update(const uint8_t* data, size_t len);
    void final(uint8_t digest[DIGEST_SIZE]);

    static void hash(const uint8_t* data, size_t len, uint8_t digest[DIGEST_SIZE]);
    static std::array<uint8_t, DIGEST_SIZE> hash(const uint8_t* data, size_t len);
    static std::string hashToHex(const uint8_t* data, size_t len);
    static std::string bytesToHex(const uint8_t* data, size_t len);

private:
    void transform(const uint8_t block[BLOCK_SIZE]);

    uint32_t m_state[8];
    uint64_t m_count;
    uint8_t m_buffer[BLOCK_SIZE];
};

} // namespace crypto
} // namespace aion

#endif // AION_SHA256_H
