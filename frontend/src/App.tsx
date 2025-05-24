import React from 'react';
import { Outlet } from 'react-router-dom'; // For rendering child routes
import Navbar from './components/Navbar';

function App() {
  return (
    <div>
      <Navbar />
      <main>
        <Outlet /> {/* Child routes will be rendered here */}
      </main>
    </div>
  );
}

export default App;
