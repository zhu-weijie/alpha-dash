// src/pages/PortfolioPage.tsx
import React, { useEffect, useState } from 'react';
import { getPortfolioSummary } from '../services/apiService';
import { PortfolioSummary, PortfolioHolding } from '../types/portfolio';
import { Link as RouterLink } from 'react-router-dom';

const PortfolioPage: React.FC = () => {
    const [portfolio, setPortfolio] = useState<PortfolioSummary | null>(null);
    const [loading, setLoading] = useState<boolean>(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const fetchPortfolio = async () => {
            try {
                setLoading(true);
                setError(null);
                const data = await getPortfolioSummary();
                setPortfolio(data);
            } catch (err: any) {
                setError(err.message || 'Failed to fetch portfolio data.');
                if (err.response && err.response.status === 401) {
                    // Handle unauthorized, e.g., clear token and redirect
                    // localStorage.removeItem('authToken');
                    // navigate('/login');
                    setError('Unauthorized. Please log in again.');
                }
            } finally {
                setLoading(false);
            }
        };

        // Check for token before fetching. If no token, redirect or show message.
        const token = localStorage.getItem('authToken');
        if (!token) {
            setError('You must be logged in to view your portfolio.');
            setLoading(false);
            return;
        }

        fetchPortfolio();
    }, []);

    if (loading) return <p>Loading portfolio...</p>;
    if (error) return <p style={{ color: 'red' }}>Error: {error}</p>;
    if (!portfolio) return <p>No portfolio data found.</p>;

    const formatCurrency = (value?: number | null) => {
        if (value === null || typeof value === 'undefined') return 'N/A';
        return value.toLocaleString('en-US', { style: 'currency', currency: 'USD' });
    };

    const formatPercent = (value?: number | null) => {
        if (value === null || typeof value === 'undefined') return 'N/A';
        return `${value.toFixed(2)}%`;
    }

    return (
        <div>
            <h2>My Portfolio</h2>
            
            <div style={{ marginBottom: '20px', border: '1px solid #ccc', padding: '10px' }}>
                <h4>Summary</h4>
                <p>Total Invested: {formatCurrency(portfolio.total_purchase_value)}</p>
                <p>Total Current Value: {formatCurrency(portfolio.total_current_value)}</p>
                <p>Total Gain/Loss: {formatCurrency(portfolio.total_gain_loss)} 
                   <span style={{ color: (portfolio.total_gain_loss ?? 0) >= 0 ? 'green' : 'red', marginLeft: '10px' }}>
                       ({formatPercent(portfolio.total_gain_loss_percent)})
                   </span>
                </p>
            </div>

            <h3>Holdings</h3>
            {portfolio.holdings.length === 0 ? (
                <p>You have no holdings in your portfolio yet.</p>
            ) : (
                <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                    <thead>
                        <tr>
                            <th style={thStyle}>Asset</th>
                            <th style={thStyle}>Symbol</th>
                            <th style={thStyle}>Quantity</th>
                            <th style={thStyle}>Avg. Purchase Price</th>
                            <th style={thStyle}>Purchase Value</th>
                            <th style={thStyle}>Current Price</th>
                            <th style={thStyle}>Current Value</th>
                            <th style={thStyle}>Gain/Loss</th>
                            <th style={thStyle}>Gain/Loss %</th>
                        </tr>
                    </thead>
                    <tbody>
                        {portfolio.holdings.map((holding: PortfolioHolding) => {
                            const purchaseValue = holding.quantity * holding.purchase_price;
                            return (
                                <tr key={holding.id}>
                                    <td style={tdStyle}>{holding.asset_info?.name || 'N/A'}</td>
                                    <td style={tdStyle}>
                                        {holding.asset_info?.symbol ? (
                                            <RouterLink to={`/assets/${holding.asset_info.symbol}/chart`}>
                                                {holding.asset_info.symbol}
                                            </RouterLink>
                                        ) : 'N/A'}
                                    </td>
                                    <td style={tdStyle}>{holding.quantity.toFixed(4)}</td>
                                    <td style={tdStyle}>{formatCurrency(holding.purchase_price)}</td>
                                    <td style={tdStyle}>{formatCurrency(purchaseValue)}</td>
                                    <td style={tdStyle}>{formatCurrency(holding.current_price)}</td>
                                    <td style={tdStyle}>{formatCurrency(holding.current_value)}</td>
                                    <td style={{...tdStyle, color: (holding.gain_loss ?? 0) >= 0 ? 'green' : 'red' }}>
                                        {formatCurrency(holding.gain_loss)}
                                    </td>
                                    <td style={{...tdStyle, color: (holding.gain_loss ?? 0) >= 0 ? 'green' : 'red' }}>
                                        {formatPercent(holding.gain_loss_percent)}
                                    </td>
                                </tr>
                            );
                        })}
                    </tbody>
                </table>
            )}
        </div>
    );
};

const thStyle: React.CSSProperties = { border: '1px solid #ddd', padding: '8px', textAlign: 'left', backgroundColor: '#f2f2f2' };
const tdStyle: React.CSSProperties = { border: '1px solid #ddd', padding: '8px', textAlign: 'left' };

export default PortfolioPage;
