// src/App.tsx
import React from 'react';
import { BrowserRouter as Router, Route, Routes, Link, Navigate } from 'react-router-dom';
import { ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';
import PortfolioPage from './pages/PortfolioPage';
import AssetDetailPage from './pages/AssetDetailPage';
import ManageAssetsPage from './pages/ManageAssetsPage';

const isAuthenticated = () => !!localStorage.getItem('authToken');

interface ProtectedRouteProps {
  children: React.ReactNode;
}

const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ children }) => {
  if (!isAuthenticated()) {
      return <Navigate to="/login" replace />;
  }
  return <>{children}</>;
};

function App() {
    const handleLogout = () => {
        localStorage.removeItem('authToken');
        window.location.reload();
    };

    return (
        <Router>
            <div>
                <nav>
                    <ul style={{ listStyleType: 'none', padding: 0, display: 'flex', gap: '10px' }}>
                        <li><Link to="/">Home</Link></li>
                        {!isAuthenticated() && <li><Link to="/login">Login</Link></li>}
                        {!isAuthenticated() && <li><Link to="/register">Register</Link></li>}
                        {isAuthenticated() && <li><Link to="/portfolio">My Portfolio</Link></li>}
                        {isAuthenticated() && <li><Link to="/manage-assets">Manage Assets</Link></li>}
                        {isAuthenticated() && <li><button onClick={handleLogout}>Logout</button></li>}
                    </ul>
                </nav>
                <hr />
                <Routes>
                    <Route 
                        path="/portfolio" 
                        element={
                            <ProtectedRoute>
                                <PortfolioPage />
                            </ProtectedRoute>
                        } 
                    />
                    <Route 
                        path="/assets/:symbol/chart"
                        element={
                            <ProtectedRoute>
                                <AssetDetailPage />
                            </ProtectedRoute>
                        }
                    />
                    <Route 
                        path="/manage-assets"
                        element={
                            <ProtectedRoute>
                                <ManageAssetsPage />
                            </ProtectedRoute>
                        }
                    />
                    <Route path="/" element={<div><h1>Welcome to AlphaDash</h1><p>Please log in to see your portfolio.</p></div>} />
                    <Route path="/login" element={<div><h2>Login Page Placeholder</h2><p>Implement actual login form here which sets 'authToken' in localStorage.</p><button onClick={() => { localStorage.setItem('authToken', 'fake-test-token'); window.location.href = '/portfolio';}}>Simulate Login</button></div>} />

                </Routes>
                <ToastContainer
                    position="top-right"
                    autoClose={5000}
                    hideProgressBar={false}
                    newestOnTop={false}
                    closeOnClick
                    rtl={false}
                    pauseOnFocusLoss
                    draggable
                    pauseOnHover
                    theme="colored"
                />
            </div>
        </Router>
    );
}
export default App;
