import React from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import '@codexsun/ui/globals.css'
import App from './App'

createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <BrowserRouter basename="/logicx-app">
      <App />
    </BrowserRouter>
  </React.StrictMode>,
)
