// src/pages/PortfolioPage.tsx
import React, { useEffect, useState, useCallback } from 'react';
import { getPortfolioSummary, addPortfolioHolding, updatePortfolioHolding, deletePortfolioHolding, getUserAssetSummary } from '../services/apiService';
import { PortfolioSummary, PortfolioHolding, PortfolioHoldingUpdatePayload, BackendPortfolioHoldingCreate } from '../types/portfolio';
import { UserAssetSummaryItem } from '../types/userSummary';
import HoldingForm from '../components/Portfolio/HoldingForm';
import { Link as RouterLink } from 'react-router-dom';
import Spinner from '../components/Common/Spinner';
import { notifySuccess } from '../utils/notifications';

const thStyle: React.CSSProperties = { border: '1px solid #ddd', padding: '8px', textAlign: 'left', backgroundColor: '#f2f2f2' };
const tdStyle: React.CSSProperties = { border: '1px solid #ddd', padding: '8px', textAlign: 'left' };


const PortfolioPage: React.FC = () => {
    const [portfolio, setPortfolio] = useState<PortfolioSummary | null>(null);
    const [aggregatedSummary, setAggregatedSummary] = useState<UserAssetSummaryItem[] | null>(null);
    const [loading, setLoading] = useState<boolean>(true);
    const [error, setError] = useState<string | null>(null);
    
    const [isFormModalOpen, setIsFormModalOpen] = useState<boolean>(false);
    const [formMode, setFormMode] = useState<'add' | 'edit'>('add');
    const [currentEditingHolding, setCurrentEditingHolding] = useState<PortfolioHolding | null>(null);

    const fetchPageData = useCallback(async () => {
        try {
            setLoading(true);
            setError(null);
            const [portfolioSum, aggregatedAssetSum] = await Promise.all([
                getPortfolioSummary(),
                getUserAssetSummary()
            ]);
            setPortfolio(portfolioSum);
            setAggregatedSummary(aggregatedAssetSum);
        } catch (err: any) {
            setError(err.message || 'Failed to fetch portfolio data.');
            if (err.response && err.response.status === 401) {
                setError('Unauthorized. Please log in again.');
            }
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        const token = localStorage.getItem('authToken');
        if (!token) {
            setError('You must be logged in to view your portfolio.');
            setLoading(false);
            return;
        }
        fetchPageData();
    }, [fetchPageData]);

    const formSubmitSuccessCallback = () => {
        fetchPageData();
        setIsFormModalOpen(false);
    };

    const handleAddHoldingSubmit = async (data: BackendPortfolioHoldingCreate | PortfolioHoldingUpdatePayload) => {
        await addPortfolioHolding(data as BackendPortfolioHoldingCreate);
        formSubmitSuccessCallback();
    };

    const handleEditHoldingSubmit = async (data: BackendPortfolioHoldingCreate | PortfolioHoldingUpdatePayload) => {
        if (currentEditingHolding) {
            await updatePortfolioHolding(currentEditingHolding.id, data as PortfolioHoldingUpdatePayload);
            formSubmitSuccessCallback();
        }
    };

    const openEditModal = (holding: PortfolioHolding) => {
        setFormMode('edit');
        setCurrentEditingHolding(holding);
        setIsFormModalOpen(true);
    };

    const handleDeleteHolding = async (holdingId: number) => {
        if (window.confirm("Are you sure you want to delete this holding?")) {
            try {
                setError(null);
                await deletePortfolioHolding(holdingId);
                notifySuccess("Holding deleted successfully!");
                fetchPageData();
            } catch (err: any) {
                setError(err.response?.data?.detail || err.message || "Failed to delete holding.");
            }
        }
    };
    
    if (loading && !isFormModalOpen) {
        return (
            <div style={{ display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center', minHeight: '200px' }}>
                <Spinner size={60} />
                <p>Loading portfolio...</p>
            </div>
        );
    }
    if (error && !isFormModalOpen) return <p style={{ color: 'red' }}>Error: {error}</p>;
    if (!portfolio) return <p>No portfolio data found.</p>;

    const formatCurrency = (value?: number | null) => {
        if (value === null || typeof value === 'undefined') return 'N/A';
        return value.toLocaleString('en-US', { style: 'currency', currency: 'USD' });
    };

    const formatPercent = (value?: number | null) => {
        if (value === null || typeof value === 'undefined') return 'N/A';
        return `${value.toFixed(2)}%`;
    }

    const formatQuantity = (value?: number | null) => {
        if (value === null || typeof value === 'undefined') return 'N/A';
        return value.toFixed(4);
    };

    return (
        <div>
            <h2>My Portfolio</h2>
            <button onClick={() => setIsFormModalOpen(true)} style={{ marginBottom: '20px' }}>
                Add New Holding
            </button>
            
            <HoldingForm
                isOpen={isFormModalOpen} 
                onClose={() => setIsFormModalOpen(false)}
                onSubmitForm={formMode === 'add' ? handleAddHoldingSubmit : handleEditHoldingSubmit}
                initialData={
                    formMode === 'edit' && currentEditingHolding ? 
                    { 
                        quantity: currentEditingHolding.quantity,
                        purchase_price: currentEditingHolding.purchase_price,
                        purchase_date: currentEditingHolding.purchase_date,
                    } : undefined
                }
                mode={formMode}
                assetSymbolReadOnly={formMode === 'edit' ? currentEditingHolding?.asset_info?.symbol : undefined}
            />
            
            {portfolio ? (
                <>
                    <h3>Summary</h3>
                    <p>Total Invested: {formatCurrency(portfolio.total_purchase_value)}</p>
                    <p>Total Current Value: {formatCurrency(portfolio.total_current_value)}</p>
                    <p>Total Gain/Loss: {formatCurrency(portfolio.total_gain_loss)} 
                        <span style={{ color: (portfolio.total_gain_loss ?? 0) >= 0 ? 'green' : 'red', marginLeft: '10px' }}>
                            ({formatPercent(portfolio.total_gain_loss_percent)})
                        </span>
                    </p>

                    <h3>Aggregated Asset Positions</h3>
                    {aggregatedSummary && aggregatedSummary.length > 0 ? (
                        <table style={{ width: '100%', borderCollapse: 'collapse', marginBottom: '30px' }}>
                            <thead>
                                <tr>
                                    <th style={thStyle}>Asset</th>
                                    <th style={thStyle}>Symbol</th>
                                    <th style={thStyle}>Type</th>
                                    <th style={thStyle}>Total Quantity</th>
                                    <th style={thStyle}>Avg. Purchase Price</th>
                                </tr>
                            </thead>
                            <tbody>
                                {aggregatedSummary.map((item: UserAssetSummaryItem) => (
                                    <tr key={item.asset_id}>
                                        <td style={tdStyle}>{item.name || 'N/A'}</td>
                                        <td style={tdStyle}>
                                            <RouterLink to={`/assets/${item.symbol}/chart`}>
                                                {item.symbol}
                                            </RouterLink>
                                        </td>
                                        <td style={tdStyle}>{item.asset_type}</td>
                                        <td style={tdStyle}>{formatQuantity(item.total_quantity)}</td>
                                        <td style={tdStyle}>{formatCurrency(item.weighted_average_purchase_price)}</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    ) : (
                        <p>No aggregated asset data to display.</p>
                    )}

                    <h3>Detailed Holdings</h3>
                    {portfolio && portfolio.holdings.length === 0 ? (
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
                                    <th style={thStyle}>Actions</th>
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
                                            <td style={tdStyle}>
                                                <button onClick={() => openEditModal(holding)}>Edit</button>
                                                <button onClick={() => handleDeleteHolding(holding.id)} style={{ marginLeft: '5px', backgroundColor: '#dc3545', color: 'white'}}>Delete</button>
                                            </td>
                                        </tr>
                                    );
                                })}
                            </tbody>
                        </table>
                    )}
                </>
            ) : (
                 !loading && <p>No portfolio data available. Try adding some holdings!</p>
            )}
        </div>
    );
};

export default PortfolioPage;
