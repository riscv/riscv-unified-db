#pragma once
#include <cstdint>
#include <fmt/core.h>

#include "udb/iss_soc_model.hpp"


typedef struct _SYSCALLBLOCK
{
  uint64_t id;
  uint64_t a[7];
} SYSCALLBLOCK, *PSYSCALLBLOCK;

struct HTIFCOMMAND
{
  uint64_t value = 0;

  constexpr HTIFCOMMAND() = default;

  constexpr explicit HTIFCOMMAND(uint64_t val) : value(val) {}

  constexpr HTIFCOMMAND(uint8_t dev, uint8_t cmd, uint64_t pay)
      : value((static_cast<uint64_t>(dev) << 56) |
              (static_cast<uint64_t>(cmd) << 48) |
              (pay & 0x0000ffffffffffffULL)) {}

  constexpr uint64_t payload() const
  {
    return value & 0x0000ffffffffffffULL;
  }

  constexpr uint8_t command() const
  {
    return static_cast<uint8_t>((value >> 48) & 0xff);
  }

  constexpr uint8_t device() const
  {
    return static_cast<uint8_t>((value >> 56) & 0xff);
  }

  constexpr void set_payload(uint64_t pay)
  {
    value = (value & ~0x0000ffffffffffffULL) | (pay & 0x0000ffffffffffffULL);
  }

  constexpr void set_command(uint8_t cmd)
  {
    value = (value & ~(0xffULL << 48)) | (static_cast<uint64_t>(cmd) << 48);
  }

  constexpr void set_device(uint8_t dev)
  {
    value = (value & ~(0xffULL << 56)) | (static_cast<uint64_t>(dev) << 56);
  }

  static constexpr HTIFCOMMAND from_value(uint64_t val)
  {
    return HTIFCOMMAND(val);
  }

  static constexpr HTIFCOMMAND encode(uint8_t dev, uint8_t cmd, uint64_t pay)
  {
    return HTIFCOMMAND(dev, cmd, pay);
  }

  constexpr uint64_t to_value() const
  {
    return value;
  }

  constexpr operator uint64_t() const
  {
    return value;
  }
};

//HTIF Device base class
class HTIFDevice
{
public:
  HTIFDevice(udb::IssSocModel* pSoC);
  ~HTIFDevice();

  virtual int HandleCommand(HTIFCOMMAND cmd) = 0;
protected:
  udb::IssSocModel* m_pSoC;
};

//SysCall Device
class SysCallDevice;
typedef int (SysCallDevice::*SYSCALLHANDLER)(uint64_t a0, uint64_t a1, uint64_t a2, uint64_t a3,
                                             uint64_t a4, uint64_t a5, uint64_t a6);


class SysCallDevice : public HTIFDevice
{
public:
  SysCallDevice(udb::IssSocModel* pSoC);
  ~SysCallDevice();

  class Pass : public udb::ExitEvent
  {
  public:
    Pass() : udb::ExitEvent(0) {}

    const char* what() const noexcept override { return "Pass"; }
  };

  class Fail : public udb::ExitEvent
  {
  public:
    Fail(uint64_t testnum) : udb::ExitEvent(-1), m_testnum(testnum) {}

    const char* what() const noexcept override
    {
      return strdup(fmt::format("Test #{} failed", m_testnum).c_str());
    }
  private:
    uint64_t m_testnum;
  };

  virtual int HandleCommand(HTIFCOMMAND cmd) override;

protected:
  int exit(uint64_t a0, uint64_t a1, uint64_t a2, uint64_t a3, uint64_t a4, uint64_t a5, uint64_t a6);

  std::vector<SYSCALLHANDLER> m_cmdHandlers;
};

class BCDDevice : public HTIFDevice
{
public:
  BCDDevice(udb::IssSocModel* pSoC);
  ~BCDDevice();

  enum BCDCMD
  {
    READ = 0,
    WRITE
  };

  virtual int HandleCommand(HTIFCOMMAND cmd) override;
};


class HostTargetInterface
{
public:
  HostTargetInterface(udb::IssSocModel* pSoC, uint64_t toHostAddress, uint64_t fromHostAddress, uint64_t sigAddress, uint64_t sigLength);
  ~HostTargetInterface();

private:
  static int NotificationCallback(void* pUserParam, uint64_t uiModuleId, uint64_t uiEvent, void* pData);
  int HandleCommand(HTIFCOMMAND cmd);

  udb::IssSocModel* m_pSoC;
  uint64_t m_toHost;
  uint64_t m_fromHost;
  uint64_t m_sigAddress;
  uint64_t m_sigLength;
  std::vector<HTIFDevice*> m_devices;
  size_t m_nDevices;
  SysCallDevice m_sysCall;
  BCDDevice m_bcd;
};
