#pragma once
#include <stdint.h>

class NotificationHandler;
typedef int (*NOTIFYCALLBACK)(NotificationHandler& handler, uint64_t uiEvent, void* pData);

class NotificationHandler
{
public:
  NotificationHandler(NOTIFYCALLBACK notifyCallback = nullptr);
  ~NotificationHandler();

  void EnableEvent(uint64_t event);
  void DisableEvent(uint64_t event);
  int Notify(uint64_t uiEvent, void* pData);
  void DisableNotifications();
  void EnableNotifications();


protected:
  virtual int OnNotification(uint64_t uiEvent, void* pData) {return 0;}

  uint64_t m_uiEventMask;
  NOTIFYCALLBACK m_notifyCallback;
  bool m_bEnable;

};
