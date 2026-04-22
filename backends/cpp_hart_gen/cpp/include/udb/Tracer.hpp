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
}
