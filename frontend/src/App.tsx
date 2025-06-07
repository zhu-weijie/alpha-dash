// src/App.tsx
import React from 'react';
import { BrowserRouter as Router, Route, Routes, Link, Navigate } from 'react-router-dom';
import PortfolioPage from './pages/PortfolioPage';
// import LoginPage from './pages/LoginPage';
// import RegisterPage from './pages/RegisterPage';
// import HomePage from './pages/HomePage';

const isAuthenticated = () => !!localStorage.getItem('authToken');

interface ProtectedRouteProps {
  children: React.ReactNode; // Use React.ReactNode for more flexibility
}

const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ children }) => {
  if (!isAuthenticated()) {
      return <Navigate to="/login" replace />;
  }
  // If children can be other things than JSX.Element, you might need to wrap it
  // but if you always pass a component like <PortfolioPage />, it should be fine.
  // For safety, you can return <>{children}</> if children might be a string or number.
  return <>{children}</>; // Using a fragment <> is safe and common
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
                        {isAuthenticated() && <li><button onClick={handleLogout}>Logout</button></li>}
                    </ul>
                </nav>
                <hr />
                <Routes>
                    {/* <Route path="/" element={<HomePage />} /> */}
                    {/* <Route path="/login" element={<LoginPage />} /> */}
                    {/* <Route path="/register" element={<RegisterPage />} /> */}
                    <Route 
                        path="/portfolio" 
                        element={
                            <ProtectedRoute>
                                <PortfolioPage />
                            </ProtectedRoute>
                        } 
                    />
                    <Route path="/" element={<div><h1>Welcome to AlphaDash</h1><p>Please log in to see your portfolio.</p></div>} />
                    <Route path="/login" element={<div><h2>Login Page Placeholder</h2><p>Implement actual login form here which sets 'authToken' in localStorage.</p><button onClick={() => { localStorage.setItem('authToken', 'fake-test-token'); window.location.href = '/portfolio';}}>Simulate Login</button></div>} />

                </Routes>
            </div>
        </Router>
    );
}
export default App;
