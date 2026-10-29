#include <catch2/catch_test_macros.hpp>
#include <cstdint>
#include <vector>
#include <string>

#include "udb/endian.hpp"
#include "udb/htif.hpp"
#include "udb/iss_soc_model.hpp"
#include "udb/memory.hpp"
#include "udb/GDBServer.hpp"

using namespace udb;

namespace {
class TestConcreteMemory : public udb::Memory {
 public:
  TestConcreteMemory(uint64_t base, size_t size)
      : m_base(base), m_storage(size, 0) {}

  const std::vector<uint8_t>& storage() const { return m_storage; }

  uint8_t get_stored_byte(uint64_t addr) const {
    return m_storage.at(addr - m_base);
  }

 protected:
  uint8_t read1(uint64_t addr) override {
    return m_storage.at(addr - m_base);
  }
  uint16_t read2(uint64_t addr) override {
    return udb::read_le16(&m_storage.at(addr - m_base));
  }
  uint32_t read4(uint64_t addr) override {
    return udb::read_le32(&m_storage.at(addr - m_base));
  }
  uint64_t read8(uint64_t addr) override {
    return udb::read_le64(&m_storage.at(addr - m_base));
  }

  void write1(uint64_t addr, uint8_t data) override {
    m_storage.at(addr - m_base) = data;
  }
  void write2(uint64_t addr, uint16_t data) override {
    udb::write_le16(&m_storage.at(addr - m_base), data);
  }
  void write4(uint64_t addr, uint32_t data) override {
    udb::write_le32(&m_storage.at(addr - m_base), data);
  }
  void write8(uint64_t addr, uint64_t data) override {
    udb::write_le64(&m_storage.at(addr - m_base), data);
  }

 private:
  uint64_t m_base;
  std::vector<uint8_t> m_storage;
};

class TestGDBServer : public GDBServer {
 public:
  TestGDBServer() : GDBServer(GDB_SUPPORT_BASE, 0, false) {}

  REGISTERFILE writtenRegs{};
  REGISTERFILE regsToRead{};
  int writeGprCalls = 0;
  int writeSingleCalls = 0;
  int readGprCalls = 0;
  int readSingleCalls = 0;
  int lastSingleReg = -1;
  uint64_t lastSingleValue = 0;
  int lastError = 0;
  std::string lastResponse;

  int Handle(GDBPacket& packet) {
    return HandlePacket(packet);
  }

 protected:
  int OnReadGPR(REGISTERFILE& registerFile) override {
    registerFile = regsToRead;
    readGprCalls++;
    return 0;
  }

  int OnReadSingleRegister(int reg, uint64_t& value) override {
    if (reg >= 0 && reg < NUM_XREGS) {
      value = regsToRead.xReg[reg];
      readSingleCalls++;
      return 0;
    }
    return -1;
  }

  int OnWriteGPR(REGISTERFILE& registerFile) override {
    writtenRegs = registerFile;
    writeGprCalls++;
    return 0;
  }

  int OnWriteSingleRegister(int reg, uint64_t& value) override {
    if (reg >= 0 && reg < NUM_XREGS) {
      writtenRegs.xReg[reg] = value;
      lastSingleReg = reg;
      lastSingleValue = value;
      writeSingleCalls++;
      return 0;
    }
    return -1;
  }

  int SendResponse(const std::string& str) override {
    lastResponse = str;
    return 0;
  }

  int SendResponse(void* pBuffer, unsigned int len) override {
    lastResponse = std::string(static_cast<char*>(pBuffer), len);
    return 0;
  }

  int SendResponse(GDBPacket& packet) override {
    lastResponse = std::string((char*)(unsigned char*)packet, packet.Length());
    return 0;
  }

 public:
  int SendError(int error) override {
    lastError = error;
    return GDBServer::SendError(error);
  }
};

std::string format_gdb_packet(const std::string& payload) {
  uint8_t csum = 0;
  for (unsigned char c : payload) {
    csum += c;
  }
  char hex[3];
  snprintf(hex, sizeof(hex), "%02x", csum);
  return "$" + payload + "#" + hex;
}
}  // namespace

TEST_CASE("LittleEndian Helpers", "[endian]") {
  SECTION("16-bit little-endian read") {
    const uint8_t bytes[] = {0x6f, 0x00, 0x40, 0x05};
    REQUIRE(read_le16(bytes) == 0x006f);
    REQUIRE(read_le16(bytes + 2) == 0x0540);
  }

  SECTION("32-bit little-endian read") {
    const uint8_t bytes[] = {0x13, 0x05, 0x10, 0x00};
    REQUIRE(read_le32(bytes) == 0x00100513);
  }

  SECTION("64-bit little-endian read") {
    const uint8_t bytes[] = {0x01, 0x23, 0x45, 0x67, 0x89, 0xab, 0xcd, 0xef};
    REQUIRE(read_le64(bytes) == 0xefcdab8967452301ULL);
  }

  SECTION("16-bit little-endian write") {
    uint8_t bytes[2] = {0};
    write_le16(bytes, 0x1234);
    REQUIRE(bytes[0] == 0x34);
    REQUIRE(bytes[1] == 0x12);
  }

  SECTION("32-bit little-endian write") {
    uint8_t bytes[4] = {0};
    write_le32(bytes, 0x11223344);
    REQUIRE(bytes[0] == 0x44);
    REQUIRE(bytes[1] == 0x33);
    REQUIRE(bytes[2] == 0x22);
    REQUIRE(bytes[3] == 0x11);
  }

  SECTION("64-bit little-endian write") {
    uint8_t bytes[8] = {0};
    write_le64(bytes, 0x0123456789abcdefULL);
    REQUIRE(bytes[0] == 0xef);
    REQUIRE(bytes[1] == 0xcd);
    REQUIRE(bytes[2] == 0xab);
    REQUIRE(bytes[3] == 0x89);
    REQUIRE(bytes[4] == 0x67);
    REQUIRE(bytes[5] == 0x45);
    REQUIRE(bytes[6] == 0x23);
    REQUIRE(bytes[7] == 0x01);
  }

  SECTION("Roundtrip reads and writes") {
    uint8_t buf[16] = {0};
    write_le16(buf, 0xbeef);
    REQUIRE(read_le16(buf) == 0xbeef);

    write_le32(buf + 2, 0xdeadbeef);
    REQUIRE(read_le32(buf + 2) == 0xdeadbeef);

    write_le64(buf + 8, 0x0102030405060708ULL);
    REQUIRE(read_le64(buf + 8) == 0x0102030405060708ULL);
  }
}

TEST_CASE("IssSocModel Little-Endian Operations", "[memory][iss_soc_model]") {
  const uint64_t base = 0x80000000ULL;
  const uint64_t size = 4096;
  IssSocModel soc(size, base);

  SECTION("Read known byte patterns") {
    const uint8_t test_data[] = {
      0x6f, 0x00, 0x40, 0x05,  // j 0x80000580 (0x0540006f)
      0x13, 0x05, 0x10, 0x00,  // addi a0, zero, 1 (0x00100513)
    };
    soc.memcpy_from_host(base, test_data, sizeof(test_data));

    // 1-byte read
    REQUIRE(soc.read_physical_memory_8(base) == 0x6f);
    REQUIRE(soc.read_physical_memory_8(base + 1) == 0x00);

    // 16-bit read: 6f 00 -> 0x006f
    REQUIRE(soc.read_physical_memory_16(base) == 0x006f);

    // 32-bit read: 13 05 10 00 -> 0x00100513
    REQUIRE(soc.read_physical_memory_32(base + 4) == 0x00100513);

    // 64-bit read of all 8 bytes
    REQUIRE(soc.read_physical_memory_64(base) == 0x001005130540006fULL);
  }

  SECTION("Write produces expected little-endian bytes") {
    soc.write_physical_memory_32(base + 0x100, 0x11223344);

    uint8_t readback[4] = {0};
    soc.memcpy_to_host(readback, base + 0x100, 4);
    REQUIRE(readback[0] == 0x44);
    REQUIRE(readback[1] == 0x33);
    REQUIRE(readback[2] == 0x22);
    REQUIRE(readback[3] == 0x11);
  }

  SECTION("Roundtrip reads and writes for 16, 32, and 64 bits") {
    soc.write_physical_memory_16(base + 10, 0xa55a);
    REQUIRE(soc.read_physical_memory_16(base + 10) == 0xa55a);

    soc.write_physical_memory_32(base + 20, 0x12345678);
    REQUIRE(soc.read_physical_memory_32(base + 20) == 0x12345678);

    soc.write_physical_memory_64(base + 32, 0xfedcba9876543210ULL);
    REQUIRE(soc.read_physical_memory_64(base + 32) == 0xfedcba9876543210ULL);
  }

  SECTION("Unaligned access support") {
    soc.write_physical_memory_16(base + 1, 0x1234);
    REQUIRE(soc.read_physical_memory_16(base + 1) == 0x1234);

    soc.write_physical_memory_32(base + 3, 0x87654321);
    REQUIRE(soc.read_physical_memory_32(base + 3) == 0x87654321);

    soc.write_physical_memory_64(base + 7, 0x0123456789abcdefULL);
    REQUIRE(soc.read_physical_memory_64(base + 7) == 0x0123456789abcdefULL);
  }

  SECTION("Boundary access at edges of memory") {
    soc.write_physical_memory_8(base, 0xaa);
    REQUIRE(soc.read_physical_memory_8(base) == 0xaa);

    soc.write_physical_memory_64(base + size - 8, 0x1122334455667788ULL);
    REQUIRE(soc.read_physical_memory_64(base + size - 8) == 0x1122334455667788ULL);
  }

  SECTION("IssSocModel public memory interface direct values") {
    soc.write_physical_memory_8(base + 0x200, 0x77);
    REQUIRE(soc.read_physical_memory_8(base + 0x200) == 0x77);

    soc.write_physical_memory_16(base + 0x202, 0x1234);
    REQUIRE(soc.read_physical_memory_16(base + 0x202) == 0x1234);

    soc.write_physical_memory_32(base + 0x204, 0x89abcdef);
    REQUIRE(soc.read_physical_memory_32(base + 0x204) == 0x89abcdef);

    soc.write_physical_memory_64(base + 0x208, 0x0123456789abcdefULL);
    REQUIRE(soc.read_physical_memory_64(base + 0x208) == 0x0123456789abcdefULL);
  }

  SECTION("First and last valid memory locations and out-of-bounds safety") {
    // First byte
    soc.write_physical_memory_8(base, 0x12);
    REQUIRE(soc.read_physical_memory_8(base) == 0x12);

    // Last byte
    soc.write_physical_memory_8(base + size - 1, 0x34);
    REQUIRE(soc.read_physical_memory_8(base + size - 1) == 0x34);

    // Out-of-bounds memcpy_from_host rejection
    uint8_t dummy[16] = {0x55};
    REQUIRE(soc.memcpy_from_host(base - 1, dummy, 1) == -1);
    REQUIRE(soc.memcpy_from_host(base + size, dummy, 1) == -1);
    REQUIRE(soc.memcpy_from_host(0xfffffffffffffffeULL, dummy, 10) == -1);

    // Out-of-bounds memcpy_to_host rejection
    REQUIRE(soc.memcpy_to_host(dummy, base - 1, 1) == -1);
    REQUIRE(soc.memcpy_to_host(dummy, base + size, 1) == -1);
    REQUIRE(soc.memcpy_to_host(dummy, 0xfffffffffffffffeULL, 10) == -1);
  }
}

TEST_CASE("MemRegion Little-Endian Operations", "[memory][mem_region]") {
  const uint64_t base = 0x10000;
  const uint64_t size = 1024;
  MemRegion region(base, size);

  SECTION("Read known byte patterns") {
    uint8_t* ptr = region.host_pointer();
    ptr[0] = 0x6f;
    ptr[1] = 0x00;
    ptr[2] = 0x40;
    ptr[3] = 0x05;
    ptr[4] = 0x13;
    ptr[5] = 0x05;
    ptr[6] = 0x10;
    ptr[7] = 0x00;

    REQUIRE(region.read1(base) == 0x6f);
    REQUIRE(region.read2(base) == 0x006f);
    REQUIRE(region.read4(base + 4) == 0x00100513);
    REQUIRE(region.read8(base) == 0x001005130540006fULL);
  }

  SECTION("Write produces expected little-endian bytes") {
    region.write(base + 0x20, static_cast<uint32_t>(0x11223344));
    uint8_t* ptr = region.host_pointer();
    REQUIRE(ptr[0x20] == 0x44);
    REQUIRE(ptr[0x21] == 0x33);
    REQUIRE(ptr[0x22] == 0x22);
    REQUIRE(ptr[0x23] == 0x11);
  }

  SECTION("Roundtrip reads and writes") {
    region.write(base + 0x40, static_cast<uint16_t>(0xcafe));
    REQUIRE(region.read2(base + 0x40) == 0xcafe);

    region.write(base + 0x50, static_cast<uint32_t>(0xbaadf00d));
    REQUIRE(region.read4(base + 0x50) == 0xbaadf00d);

    region.write(base + 0x60, static_cast<uint64_t>(0x123456789abcdef0ULL));
    REQUIRE(region.read8(base + 0x60) == 0x123456789abcdef0ULL);
  }

  SECTION("Unaligned access") {
    region.write(base + 1, static_cast<uint16_t>(0x55aa));
    REQUIRE(region.read2(base + 1) == 0x55aa);

    region.write(base + 5, static_cast<uint32_t>(0xaabbccdd));
    REQUIRE(region.read4(base + 5) == 0xaabbccdd);

    region.write(base + 9, static_cast<uint64_t>(0x0102030405060708ULL));
    REQUIRE(region.read8(base + 9) == 0x0102030405060708ULL);
  }
}

TEST_CASE("HTIFCOMMAND Bit Positions and Consistency", "[htif]") {
  SECTION("Single 64-bit value member representation") {
    REQUIRE(sizeof(HTIFCOMMAND) == sizeof(uint64_t));

    HTIFCOMMAND cmd;
    REQUIRE(cmd.device() == 0);
    REQUIRE(cmd.command() == 0);
    REQUIRE(cmd.payload() == 0);
    REQUIRE(cmd.value == 0);
  }

  SECTION("Decode 64-bit value: device [63:56], command [55:48], payload [47:0]") {
    uint64_t raw = (0x01ULL << 56) | (0x02ULL << 48) | 0x000012345678ULL;
    HTIFCOMMAND cmd(raw);

    REQUIRE(cmd.device() == 0x01);
    REQUIRE(cmd.command() == 0x02);
    REQUIRE(cmd.payload() == 0x000012345678ULL);
    REQUIRE(cmd.value == raw);
    REQUIRE(cmd.to_value() == raw);
  }

  SECTION("Setters maintain single value consistency") {
    HTIFCOMMAND cmd;
    cmd.set_device(0x12);
    REQUIRE(cmd.device() == 0x12);
    REQUIRE(cmd.value == (0x12ULL << 56));

    cmd.set_command(0x34);
    REQUIRE(cmd.command() == 0x34);
    REQUIRE(cmd.device() == 0x12);
    REQUIRE(cmd.value == ((0x12ULL << 56) | (0x34ULL << 48)));

    cmd.set_payload(0x0000abcdef123456ULL);
    REQUIRE(cmd.payload() == 0x0000abcdef123456ULL);
    REQUIRE(cmd.command() == 0x34);
    REQUIRE(cmd.device() == 0x12);
    REQUIRE(cmd.value == ((0x12ULL << 56) | (0x34ULL << 48) | 0x0000abcdef123456ULL));
  }

  SECTION("Test pass/fail payloads") {
    // Pass is payload = 1 (testnum 0: (0 << 1) | 1)
    HTIFCOMMAND pass_cmd(1ULL);
    REQUIRE(pass_cmd.device() == 0);
    REQUIRE(pass_cmd.command() == 0);
    REQUIRE(pass_cmd.payload() == 1);
    REQUIRE((pass_cmd.payload() & 1) != 0);
    REQUIRE((pass_cmd.payload() >> 1) == 0);

    // Fail for test #42 is (42 << 1) | 1 = 85
    HTIFCOMMAND fail_cmd((42ULL << 1) | 1ULL);
    REQUIRE(fail_cmd.payload() == 85);
    REQUIRE((fail_cmd.payload() & 1) != 0);
    REQUIRE((fail_cmd.payload() >> 1) == 42);
  }

  SECTION("Encode and roundtrip") {
    uint8_t dev = 0xab;
    uint8_t cmd_code = 0xcd;
    uint64_t payload = 0x0000fedcba987654ULL;

    HTIFCOMMAND cmd = HTIFCOMMAND::encode(dev, cmd_code, payload);
    REQUIRE(cmd.device() == dev);
    REQUIRE(cmd.command() == cmd_code);
    REQUIRE(cmd.payload() == payload);
    REQUIRE(cmd.to_value() == cmd.value);

    // Decode back from value
    HTIFCOMMAND decoded(cmd.value);
    REQUIRE(decoded.device() == dev);
    REQUIRE(decoded.command() == cmd_code);
    REQUIRE(decoded.payload() == payload);
  }

  SECTION("Boundary values and oversized inputs") {
    // Max field values: device 0xff, command 0xff, payload 0x0000ffffffffffffULL
    HTIFCOMMAND max_cmd(0xff, 0xff, 0x0000ffffffffffffULL);
    REQUIRE(max_cmd.device() == 0xff);
    REQUIRE(max_cmd.command() == 0xff);
    REQUIRE(max_cmd.payload() == 0x0000ffffffffffffULL);
    REQUIRE(max_cmd.value == 0xffffffffffffffffULL);

    // Oversized payload passed to constructor is masked to 48 bits
    HTIFCOMMAND over_cmd(0x01, 0x02, 0xffffffffffffffffULL);
    REQUIRE(over_cmd.device() == 0x01);
    REQUIRE(over_cmd.command() == 0x02);
    REQUIRE(over_cmd.payload() == 0x0000ffffffffffffULL);

    // Oversized payload passed to set_payload is masked to 48 bits
    HTIFCOMMAND set_cmd;
    set_cmd.set_payload(0xffffffffffffffffULL);
    REQUIRE(set_cmd.payload() == 0x0000ffffffffffffULL);
    REQUIRE(set_cmd.device() == 0);
    REQUIRE(set_cmd.command() == 0);
  }
}

TEST_CASE("Memory::memcpy_from_host and memcpy_to_host Byte Preservation", "[memory][memcpy]") {
  const std::vector<size_t> test_sizes = {1, 7, 8, 9, 15, 16};
  const std::vector<uint64_t> guest_addresses = {0x1000ULL, 0x80001003ULL};

  for (uint64_t guest_addr : guest_addresses) {
    DYNAMIC_SECTION("Base Address 0x" << std::hex << guest_addr) {
      TestConcreteMemory mem(guest_addr - 0x100, 4096);
      IssSocModel soc(4096, guest_addr - 0x100);

      for (size_t size : test_sizes) {
        DYNAMIC_SECTION("Size " << size << " bytes") {
          std::vector<uint8_t> src(size);
          for (size_t i = 0; i < size; ++i) {
            src[i] = static_cast<uint8_t>((0xa5 + i * 17) & 0xff);
          }

          // Test udb::Memory implementation
          mem.memcpy_from_host(guest_addr, src.data(), size);
          for (size_t i = 0; i < size; ++i) {
            REQUIRE(mem.get_stored_byte(guest_addr + i) == src[i]);
          }

          std::vector<uint8_t> dst(size, 0);
          mem.memcpy_to_host(dst.data(), guest_addr, size);
          for (size_t i = 0; i < size; ++i) {
            REQUIRE(dst[i] == src[i]);
          }

          // Test IssSocModel implementation
          int written = soc.memcpy_from_host(guest_addr, src.data(), size);
          REQUIRE(written == static_cast<int>(size));

          std::vector<uint8_t> soc_dst(size, 0);
          int read_back = soc.memcpy_to_host(soc_dst.data(), guest_addr, size);
          REQUIRE(read_back == static_cast<int>(size));
          for (size_t i = 0; i < size; ++i) {
            REQUIRE(soc_dst[i] == src[i]);
          }
        }
      }
    }
  }
}

TEST_CASE("GDB Server Register Endianness and Protocol Serialization", "[gdb][endian]") {
  SECTION("Protocol checksum verification and rejection") {
    // Correct computed checksum for "qSupported" is 0x37
    std::string validPkt = format_gdb_packet("qSupported");
    GDBPacket pkt((unsigned char*)validPkt.data(), validPkt.size());
    REQUIRE(pkt.Validate() == true);

    // Corrupted checksum mismatch
    std::string corruptPkt = "$qSupported#99";
    GDBPacket badPkt((unsigned char*)corruptPkt.data(), corruptPkt.size());
    REQUIRE(badPkt.Validate() == false);

    // Missing packet start marker
    std::string noStartPkt = "qSupported#37";
    GDBPacket noStartBadPkt((unsigned char*)noStartPkt.data(), noStartPkt.size());
    REQUIRE(noStartBadPkt.Validate() == false);
  }

  SECTION("Register write endianness ($P single register, $G all registers)") {
    // Valid P packet for register 0 with genuine checksum ($P0=0102030405060708#e1)
    {
      TestGDBServer server;
      std::string raw = format_gdb_packet("P0=0102030405060708");
      GDBPacket pkt((unsigned char*)raw.data(), raw.size());
      REQUIRE(pkt.Validate() == true);
      server.Handle(pkt);
      REQUIRE(server.lastError == 0);
      REQUIRE(server.lastResponse == "OK");
      REQUIRE(server.writeSingleCalls == 1);
      REQUIRE(server.lastSingleReg == 0);
      REQUIRE(server.lastSingleValue == 0x0807060504030201ULL);
      REQUIRE(server.writtenRegs.xReg[0] == 0x0807060504030201ULL);
    }

    // Valid P packet for register 5 with genuine checksum ($P5=efcdab8967452301#24)
    {
      TestGDBServer server;
      std::string raw = format_gdb_packet("P5=efcdab8967452301");
      GDBPacket pkt((unsigned char*)raw.data(), raw.size());
      REQUIRE(pkt.Validate() == true);
      server.Handle(pkt);
      REQUIRE(server.lastError == 0);
      REQUIRE(server.lastResponse == "OK");
      REQUIRE(server.writeSingleCalls == 1);
      REQUIRE(server.lastSingleReg == 5);
      REQUIRE(server.lastSingleValue == 0x0123456789abcdefULL);
      REQUIRE(server.writtenRegs.xReg[5] == 0x0123456789abcdefULL);
    }

    // Complete 32-register G packet with genuine checksum
    {
      TestGDBServer server;
      std::string gPayload = "G";
      const char hexChars[] = "0123456789abcdef";
      for (int i = 0; i < NUM_XREGS; ++i) {
        uint64_t regVal = 0x1000000000000000ULL + static_cast<uint64_t>(i);
        uint8_t le[8];
        udb::write_le64(le, regVal);
        for (int b = 0; b < 8; ++b) {
          gPayload += hexChars[(le[b] >> 4) & 0x0f];
          gPayload += hexChars[le[b] & 0x0f];
        }
      }
      std::string raw = format_gdb_packet(gPayload);
      GDBPacket pkt((unsigned char*)raw.data(), raw.size());
      REQUIRE(pkt.Validate() == true);
      server.Handle(pkt);
      REQUIRE(server.lastError == 0);
      REQUIRE(server.lastResponse == "OK");
      REQUIRE(server.writeGprCalls == 1);
      REQUIRE(server.writtenRegs.nXRegs == NUM_XREGS);
      for (int i = 0; i < NUM_XREGS; ++i) {
        REQUIRE(server.writtenRegs.xReg[i] == (0x1000000000000000ULL + static_cast<uint64_t>(i)));
      }
    }
  }

  SECTION("Register read endianness ($p single register, $g all registers)") {
    // Single register read ($p0)
    {
      TestGDBServer server;
      server.regsToRead.xReg[0] = 0x0807060504030201ULL;
      std::string raw = format_gdb_packet("p0");
      GDBPacket pkt((unsigned char*)raw.data(), raw.size());
      REQUIRE(pkt.Validate() == true);
      server.Handle(pkt);
      REQUIRE(server.readSingleCalls == 1);
      REQUIRE(server.lastResponse == "$0102030405060708");
    }

    // Single register read ($p5)
    {
      TestGDBServer server;
      server.regsToRead.xReg[5] = 0x0123456789abcdefULL;
      std::string raw = format_gdb_packet("p5");
      GDBPacket pkt((unsigned char*)raw.data(), raw.size());
      REQUIRE(pkt.Validate() == true);
      server.Handle(pkt);
      REQUIRE(server.readSingleCalls == 1);
      REQUIRE(server.lastResponse == "$efcdab8967452301");
    }

    // Read all 32 registers ($g)
    {
      TestGDBServer server;
      server.regsToRead.nXRegs = NUM_XREGS;
      std::string expectedPayload = "$";
      const char hexChars[] = "0123456789abcdef";
      for (int i = 0; i < NUM_XREGS; ++i) {
        server.regsToRead.xReg[i] = 0x1000000000000000ULL + static_cast<uint64_t>(i);
        uint8_t le[8];
        udb::write_le64(le, server.regsToRead.xReg[i]);
        for (int b = 0; b < 8; ++b) {
          expectedPayload += hexChars[(le[b] >> 4) & 0x0f];
          expectedPayload += hexChars[le[b] & 0x0f];
        }
      }
      std::string raw = format_gdb_packet("g");
      GDBPacket pkt((unsigned char*)raw.data(), raw.size());
      REQUIRE(pkt.Validate() == true);
      server.Handle(pkt);
      REQUIRE(server.readGprCalls == 1);
      REQUIRE(server.lastResponse == expectedPayload);
    }
  }

  SECTION("SendError single-byte formatting") {
    TestGDBServer server;
    server.SendError(1);
    REQUIRE(server.lastResponse == "$E01");
    server.SendError(-1);
    REQUIRE(server.lastResponse == "$E01");
    server.SendError(255);
    REQUIRE(server.lastResponse == "$Eff");
  }
}
