// frontend/src/__mocks__/react-router-dom.tsx
import React from 'react';

export const BrowserRouter = ({ children }: { children: React.ReactNode }) => <>{children}</>;
export const Link = ({ to, children, ...rest }: { to: string; children: React.ReactNode; [key: string]: any }) => ( <a href={to} {...rest}>{children}</a> );
export const Navigate = ({ to }: { to: string }) => { return <div data-testid="mock-navigate" data-to={to}>Navigating to {to}</div>; };
export const useParams = jest.fn(() => ({}));
export const useNavigate = jest.fn(() => jest.fn());
export const useLocation = jest.fn(() => ({ pathname: '/', search: '', hash: '', state: null, key: 'default' }));
export const Outlet = () => <div data-testid="mock-outlet" />;

export const Routes = ({ children }: { children: React.ReactNode }) => <>{children}</>;

export const Route = ({ element, ...rest }: { path: string; element: React.ReactNode; [key: string]: any }) => {
    return <>{element}</>;
};
