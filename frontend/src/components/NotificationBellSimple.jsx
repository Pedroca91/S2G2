import React from 'react';
import { Bell } from 'lucide-react';
import { Button } from './ui/button';

export const NotificationBell = () => {
  return (
    <Button
      variant="ghost"
      size="icon"
      className="relative hover:bg-gray-100"
      onClick={() => console.log('Notificações desabilitadas temporariamente')}
    >
      <Bell className="h-5 w-5" />
    </Button>
  );
};

export default NotificationBell;