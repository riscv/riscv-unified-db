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

  RiscvTestsTracer::RiscvTestsTracer(HartBase<IssSocModel>* pHart, IssSocModel* pSoC, std::string& elfFilePath) :
    Tracer(pHart, pSoC)
  {
    udb::ElfReader elfReader(elfFilePath.c_str());
    //Is there a "tohost" and "fromhost" port (symbol)
    if(elfReader.getSym("tohost", &m_toHostAddress))
    {
      EnableEvent(TRACE_SOC_MODULE, udb::MEMWRITE_EVENT);
      if(elfReader.getSym("fromhost", &m_fromHostAddress))
        EnableEvent(TRACE_SOC_MODULE, udb::MEMREAD_EVENT);

      m_pSoC->AttachHandler(this, TRACE_SOC_MODULE);
    }
  }

  void RiscvTestsTracer::OnPhysicalMemoryWrite(uint64_t addr, unsigned len, uint64_t data)
  {
    //Capture writes to the "host port"
    if((len == sizeof(uint64_t) && addr == m_toHostAddress) ||
        (len == sizeof(uint32_t) && addr == (m_toHostAddress + sizeof(uint32_t))))
      {
        uint64_t toHostValue = m_pSoC->read_physical_memory_64(m_toHostAddress);

        if((toHostValue & ~(0xffUL)) == 0x0101000000000000UL) //putchar
        {
          DisableNotifications();
          m_pSoC->write_physical_memory_64(m_toHostAddress, 0);
          EnableNotifications();

          putchar((char)(toHostValue & 0xff));
        }
        else if(data < 2)
          throw Pass();
        else
          throw Fail(data >> 1);
      }
  }
}
