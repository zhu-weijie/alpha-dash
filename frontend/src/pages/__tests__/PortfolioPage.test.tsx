// src/pages/__tests__/PortfolioPage.test.tsx
import React from 'react';
import { render, screen, waitFor, act } from '@testing-library/react'; // Import act
import { BrowserRouter } from 'react-router-dom';
import PortfolioPage from '../PortfolioPage';
import * as apiService from '../../services/apiService';

jest.mock('../../services/apiService');
const mockedApiService = apiService as jest.Mocked<typeof apiService>;

// Mock localStorage
const mockLocalStorage = (() => {
    let store: { [key: string]: string } = {};
    return {
    getItem: (key: string) => store[key] || null,
    setItem: (key: string, value: string) => { store[key] = value.toString(); },
    removeItem: (key: string) => { delete store[key]; },
    clear: () => { store = {}; },
    length: 0,
    key: (index: number) => null
    };
    })();

beforeEach(() => {
    Object.defineProperty(window, 'localStorage', { value: mockLocalStorage, writable: true });
    window.localStorage.setItem('authToken', 'fake-token');
    
    // Reset mocks and provide default resolved values
    mockedApiService.getPortfolioSummary.mockResolvedValue({
        total_purchase_value: 1000, total_current_value: 1200,
        total_gain_loss: 200, total_gain_loss_percent: 20, holdings: []
    });
    mockedApiService.getUserAssetSummary.mockResolvedValue([]);
});

afterEach(() => {
    jest.clearAllMocks();
    window.localStorage.clear();
});

test('renders PortfolioPage and displays summary titles when authenticated', async () => {
    render(
        <BrowserRouter> {/* This will use your mock BrowserRouter */}
            <PortfolioPage />
        </BrowserRouter>
    );

    // More robust waiting for multiple elements that appear after async operations
    await waitFor(() => {
        expect(screen.queryByText(/Loading portfolio.../i)).not.toBeInTheDocument(); // Ensure loading is gone
    });

    // Now check for the actual content
    expect(screen.getByText(/My Portfolio/i)).toBeInTheDocument();
    expect(screen.getByText(/^Summary$/i)).toBeInTheDocument();
    expect(screen.getByText(/Aggregated Asset Positions/i)).toBeInTheDocument();
    expect(screen.getByText(/Detailed Holdings/i)).toBeInTheDocument();

    expect(mockedApiService.getPortfolioSummary).toHaveBeenCalledTimes(1);
    expect(mockedApiService.getUserAssetSummary).toHaveBeenCalledTimes(1);
});

// ... (other tests: 'displays "Add New Holding" button', 'shows unauthorized message if no token') ...
// Ensure these also use await findBy* or waitFor if checking for async content.
// For 'shows unauthorized message if no token', the error message appears synchronously 
// after the initial render if token is missing, so findByText is good there.