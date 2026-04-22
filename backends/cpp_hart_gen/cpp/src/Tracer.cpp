#include "udb/Tracer.hpp"
#include "udb/iss_soc_model.hpp"
#include "udb/elf_reader.hpp"
#include "udb/inst.hpp"

namespace udb
{
  Tracer::Tracer(HartBase<IssSocModel>* pHart, IssSocModel* pSoC)
  {
    m_pHart = pHart;
    m_pSoC = pSoC;

    //Enble events for instruction tracing
    EnableEvent(TRACE_HART_MODULE, udb::PREEXECUTE_EVENT);
    EnableEvent(TRACE_HART_MODULE, udb::EXECUTE_EVENT);

    //Attach to the Hart
    m_pHart->AttachHandler(this, TRACE_HART_MODULE);
  }

  Tracer::~Tracer()
  {

  }

  int Tracer::OnNotification(uint8_t uiModuleId, uint64_t uiEvent, void* pData)
  {
    if(uiModuleId == TRACE_HART_MODULE)
    {
      //Instruction trace
      switch(uiEvent)
      {
      case PREEXECUTE_EVENT:
        {
          udb::InstBase* pInst = (udb::InstBase*)pData;
          fmt::print("PC {:x} {}\n", m_pHart->pc(), pInst->disassemble());
          for(auto r : pInst->srcRegs())
            fmt::print("R {} {:x}\n", r.to_string(), m_pHart->xreg(r.get_num()));
        }
        break;
      case EXECUTE_EVENT:
        {
          udb::InstBase* pInst = (udb::InstBase*)pData;
          for (auto r : pInst->dstRegs())
            fmt::print("R= {} {:x}\n", r.to_string(), m_pHart->xreg(r.get_num()));
        }
        break;
      case EXCEPTION_EVENT:
        OnException();
      default:
        break;
      }
    }
    else if(uiModuleId == TRACE_SOC_MODULE)
    {
      //Memory access trace
      switch(uiEvent)
      {
      case MEMREAD_EVENT:
        if(pData != nullptr)
        {
          MemAccessRange* pMemAccessRange =  (MemAccessRange*)pData;
          OnPhysicalMemoryRead(pMemAccessRange->GetAddress(), pMemAccessRange->GetSize());
        }
        break;
      case MEMWRITE_EVENT:
        if(pData != nullptr)
        {
          MemAccess* pMemAccess =  (MemAccess*)pData;
          OnPhysicalMemoryWrite(pMemAccess->GetAddress(), pMemAccess->GetSize(), pMemAccess->GetData());
        }
        break;
      default:
        break;
      }
    }
    return 0;
  }
}
