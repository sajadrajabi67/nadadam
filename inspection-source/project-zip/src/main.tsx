import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { App as CapApp } from '@capacitor/app';
import { LocalNotifications } from '@capacitor/local-notifications';
import './index.css';
import App from './App';

// reminders.ts looks the plugin up on globalThis.Capacitor.Plugins; make sure it is registered there.
const cap = (globalThis as Record<string, any>).Capacitor;
if (cap?.Plugins && !cap.Plugins.LocalNotifications) cap.Plugins.LocalNotifications = LocalNotifications;
if (cap?.Plugins && !cap.Plugins.App) cap.Plugins.App = CapApp;

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
