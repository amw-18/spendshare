import React from 'react'
import ReactDOM from 'react-dom/client'
import { AppRouter } from './router.tsx' // Import AppRouter
import './index.css'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <AppRouter /> {/* Use AppRouter here */}
  </React.StrictMode>,
)
