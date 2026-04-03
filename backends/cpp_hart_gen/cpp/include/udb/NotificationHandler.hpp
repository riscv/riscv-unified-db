#pragma once
#include <stdint.h>
#include <stddef.h>
#include <list>

class NotificationHandler;
typedef int (*NOTIFYCALLBACK)(NotificationHandler& handler, uint8_t uiModuleId, uint64_t uiEvent, void* pData);

class NotificationHandler
{
public:
  NotificationHandler(NOTIFYCALLBACK notifyCallback = nullptr);
  ~NotificationHandler();

  virtual int Notify(uint8_t uiModuleId, uint64_t uiEvent, void* pData);
  void DisableNotifications();
  void EnableNotifications();


protected:
  virtual int OnNotification(uint8_t uiModuleId, uint64_t uiEvent, void* pData) {return 0;}

  NOTIFYCALLBACK m_notifyCallback;
  bool m_bEnable;

};

template<size_t N>
class NotificationHandlerEx : public NotificationHandler
{
public:
  NotificationHandlerEx() : NotificationHandler(nullptr)
  {
    for(int i = 0 ; i < N ; i++)
      m_uiEventMask[i] = 0;
  }

  ~NotificationHandlerEx()
  {

  }

  void EnableEvent(uint8_t uiModuleId, uint64_t event)
  {
    m_uiEventMask[uiModuleId] |= (1 << event);
  }

  void DisableEvent(uint8_t uiModuleId, uint64_t event)
  {
    m_uiEventMask[uiModuleId] &= ~(1 << event);
  }

  virtual int Notify(uint8_t uiModuleId, uint64_t uiEvent, void* pData) override
  {
    if(!m_bEnable || ((1 << uiEvent) & m_uiEventMask[uiModuleId]) == 0)
    return 0;

    if(m_notifyCallback)
      return m_notifyCallback(*this, uiModuleId, uiEvent, pData);
    else
      return OnNotification(uiModuleId, uiEvent, pData);
  }

protected:
  uint64_t m_uiEventMask[N];
};

class HandlerId
{
public:
  HandlerId(NotificationHandler* pHandler, uint8_t id)
  {
    m_pHandler = pHandler;
    m_id = id;
  }
  ~HandlerId() {};

  NotificationHandler* m_pHandler;
  uint8_t m_id;
};

class NotificationSource
{
public:
  NotificationSource();
  ~NotificationSource();

  int AttachHandler(NotificationHandler* pHandler, uint8_t id);
  int Notify(uint64_t uiEvent, void* pData);

protected:
  std::list<HandlerId> m_handlerList;
};
