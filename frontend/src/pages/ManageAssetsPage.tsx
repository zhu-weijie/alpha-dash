// src/pages/ManageAssetsPage.tsx
import React, { useState } from 'react';
import { createAsset } from '../services/apiService';
import { AssetCreatePayload, AssetType } from '../types/asset';

const ManageAssetsPage: React.FC = () => {
    const [formData, setFormData] = useState<AssetCreatePayload>({
        symbol: '',
        name: '',
        asset_type: AssetType.STOCK,
    });
    const [error, setError] = useState<string | null>(null);
    const [successMessage, setSuccessMessage] = useState<string | null>(null);
    const [loading, setLoading] = useState<boolean>(false);

    const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
        const { name, value } = e.target;
        setFormData(prev => ({
            ...prev,
            [name]: value,
        }));
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError(null);
        setSuccessMessage(null);
        setLoading(true);

        if (!formData.symbol.trim() || !formData.name.trim()) {
            setError("Symbol and Name are required.");
            setLoading(false);
            return;
        }

        try {
            const newAsset = await createAsset(formData);
            setSuccessMessage(`Asset "${newAsset.name} (${newAsset.symbol})" created successfully!`);
            setFormData({ symbol: '', name: '', asset_type: AssetType.STOCK });
        } catch (err: any) {
            setError(err.response?.data?.detail || err.message || "Failed to create asset.");
        } finally {
            setLoading(false);
        }
    };

    return (
        <div>
            <h2>Manage Assets - Create New Asset</h2>
            {error && <p style={{ color: 'red' }}>Error: {error}</p>}
            {successMessage && <p style={{ color: 'green' }}>{successMessage}</p>}
            <form onSubmit={handleSubmit} style={{ maxWidth: '400px', margin: '20px auto', padding: '20px', border: '1px solid #ccc', borderRadius: '5px' }}>
                <div style={formGroupStyle}>
                    <label htmlFor="symbol">Asset Symbol (e.g., AAPL, GOOG, BTC, ETH):</label>
                    <input type="text" id="symbol" name="symbol" value={formData.symbol} onChange={handleChange} required style={inputStyle} />
                </div>
                <div style={formGroupStyle}>
                    <label htmlFor="name">Asset Name (e.g., Apple Inc., Bitcoin):</label>
                    <input type="text" id="name" name="name" value={formData.name} onChange={handleChange} required style={inputStyle} />
                </div>
                <div style={formGroupStyle}>
                    <label htmlFor="asset_type">Asset Type:</label>
                    <select id="asset_type" name="asset_type" value={formData.asset_type} onChange={handleChange} style={inputStyle}>
                        <option value={AssetType.STOCK}>Stock</option>
                        <option value={AssetType.CRYPTO}>Cryptocurrency</option>
                    </select>
                </div>
                <button type="submit" disabled={loading} style={buttonStyle}>
                    {loading ? 'Creating...' : 'Create Asset'}
                </button>
            </form>
            {/* TODO: Add a list of existing assets here later */}
        </div>
    );
};

// Reusable basic styles
const formGroupStyle: React.CSSProperties = { marginBottom: '15px' };
const inputStyle: React.CSSProperties = { width: 'calc(100% - 12px)', padding: '8px', marginTop: '5px', border: '1px solid #ccc', borderRadius: '4px', boxSizing: 'border-box' };
const buttonStyle: React.CSSProperties = { padding: '10px 15px', border: 'none', borderRadius: '4px', cursor: 'pointer', backgroundColor: '#28a745', color: 'white', width: '100%' };

export default ManageAssetsPage;
