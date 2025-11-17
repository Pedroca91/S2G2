import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Dashboard from './pages/Dashboard';
import Cases from './pages/Cases';
import SupportPanel from './pages/SupportPanel';
import Layout from './components/Layout';
import { Toaster } from './components/ui/sonner';
import './App.css';

function App() {
  return (
    <div className="App">
      <BrowserRouter>
        <Layout>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/cases" element={<Cases />} />
            <Route path="/support" element={<SupportPanel />} />
          </Routes>
        </Layout>
      </BrowserRouter>
      <Toaster position="top-right" richColors />
    </div>
  );
}

export default App;