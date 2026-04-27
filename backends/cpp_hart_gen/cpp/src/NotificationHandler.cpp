#include "udb/NotificationHandler.hpp"

NotificationHandler::NotificationHandler(NOTIFYCALLBACK notifyCallback)
{
  m_notifyCallback = notifyCallback;
  m_uiEventMask = 0;
  m_bEnable = true;
}

NotificationHandler::~NotificationHandler()
{
}

void NotificationHandler::EnableEvent(uint64_t event)
{
  m_uiEventMask |= (1 << event);
}

void NotificationHandler::DisableEvent(uint64_t event)
{
  m_uiEventMask &= ~(1 << event);
}

void NotificationHandler::EnableNotifications()
{
  m_bEnable = true;
}

void NotificationHandler::DisableNotifications()
{
  m_bEnable = false;
}

int NotificationHandler::Notify(uint64_t uiEvent, void* pData) {
  if(!m_bEnable || ((1 << uiEvent) & m_uiEventMask) == 0)
    return 0;

  if(m_notifyCallback)
    return m_notifyCallback(*this, uiEvent, pData);
  else
    return OnNotification(uiEvent, pData);
}
