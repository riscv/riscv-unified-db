#pragma once
#include <cstdint>
#include <cstring>
#include <fmt/core.h>
#include "cpp_exceptions.hpp"
#include "NotificationHandler.hpp"
#include "hart.hpp"
#include "iss_soc_model.hpp"

enum TRACER_NOTIFY_MODULES
{
  TRACE_HART_MODULE = 0,
  TRACE_SOC_MODULE,
  TRACE_MODULE_COUNT
};
namespace udb {
  // base class for tracers; defines the tracepoints
  class Tracer : public NotificationHandlerEx<TRACE_MODULE_COUNT>
  {
   public:
    Tracer(HartBase<IssSocModel>* pHart, IssSocModel* pSoC);
    virtual ~Tracer();

    virtual void OnException() {}
    virtual void OnPhysicalMemoryRead(uint64_t addr, unsigned len) {}
    virtual void OnPhysicalMemoryWrite(uint64_t addr, unsigned len, uint64_t data) {}

  protected:
    virtual int OnNotification(uint8_t uiModuleId, uint64_t uiEvent, void* pData) override;

    HartBase<IssSocModel>* m_pHart;
    IssSocModel* m_pSoC;
  };


  class RiscvTestsTracer : public udb::Tracer {
   public:
    class Pass : public udb::ExitEvent {
     public:
      Pass() : udb::ExitEvent(0) {}

      const char* what() const noexcept override { return "Pass"; }
    };

    class Fail : public udb::ExitEvent {
     public:
      Fail(uint64_t testnum) : udb::ExitEvent(-1), m_testnum(testnum) {}

      const char* what() const noexcept override {
        return strdup(fmt::format("Test #{} failed", m_testnum).c_str());
      }

     private:
      uint64_t m_testnum;
    };

    class TestnumUnInit : public udb::ExitEvent {
     public:
      TestnumUnInit() : udb::ExitEvent(-1) {}

      const char* what() const noexcept override { return "Test failed, testnum unitialized"; }
    };

   public:
    RiscvTestsTracer(HartBase<IssSocModel>* pHart, IssSocModel* pSoC, std::string& elfFilePath);


    virtual void OnPhysicalMemoryRead(uint64_t addr, unsigned len) override {};
    virtual void OnPhysicalMemoryWrite(uint64_t addr, unsigned len, uint64_t data) override;

    /*
    void trace_exception() override {
      auto cause = m_hart->_csrContainer().mcause._hw_read();
      if (cause.get() == udb::ExceptionCode::Mcall || cause.get() == udb::ExceptionCode::Scall ||
          cause.get() == udb::ExceptionCode::Ucall) {
        auto a7 = m_hart->_xreg(17);
        if (a7 == 93_b) {
          auto gp = m_hart->_xreg(3);
          if (gp == 1_b) {
            throw Pass();
          } else {
            auto testnum = m_hart->_xreg(10) >> 1_b;
            if (testnum.unknown_mask() != 0_b) {
              throw Fail(testnum.get());
            } else {
              throw TestnumUnInit();
            }
          }
        }
      }
    }
    */

   protected:
    uint64_t m_toHostAddress;
    uint64_t m_fromHostAddress;
  };
}
