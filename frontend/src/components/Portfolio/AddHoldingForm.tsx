// src/components/Portfolio/AddHoldingForm.tsx
import React, { useState } from 'react';
import { getAssetBySymbol, addPortfolioHolding } from '../../services/apiService';
import { PortfolioHoldingCreatePayload, BackendPortfolioHoldingCreate } from '../../types/portfolio';
import { Asset } from '../../types/asset';

interface AddHoldingFormProps {
    isOpen: boolean;
    onClose: () => void;
    onHoldingAdded: () => void;
}

const AddHoldingForm: React.FC<AddHoldingFormProps> = ({ isOpen, onClose, onHoldingAdded }) => {
    const [formData, setFormData] = useState<PortfolioHoldingCreatePayload>({
        symbol: '',
        quantity: 0,
        purchase_price: 0,
        purchase_date: new Date().toISOString().split('T')[0],
    });
    const [error, setError] = useState<string | null>(null);
    const [loading, setLoading] = useState<boolean>(false);

    const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const { name, value, type } = e.target;
        setFormData(prev => ({
            ...prev,
            [name]: type === 'number' ? parseFloat(value) || 0 : value,
        }));
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError(null);
        setLoading(true);

        if (!formData.symbol || formData.quantity <= 0 || formData.purchase_price < 0) {
            setError("Please fill in all required fields correctly (Symbol, Quantity > 0, Price >= 0).");
            setLoading(false);
            return;
        }

        try {
            // 1. Get asset_id from symbol
            const asset: Asset | null = await getAssetBySymbol(formData.symbol);
            if (!asset) {
                setError(`Asset with symbol "${formData.symbol}" not found. Please create it first or check spelling.`);
                setLoading(false);
                return;
            }

            // 2. Prepare backend payload
            const backendPayload: BackendPortfolioHoldingCreate = {
                asset_id: asset.id,
                quantity: formData.quantity,
                purchase_price: formData.purchase_price,
                // Backend expects ISO datetime string. Append time for full ISO compatibility.
                purchase_date: new Date(formData.purchase_date + "T00:00:00.000Z").toISOString(),
            };

            // 3. Add the holding
            await addPortfolioHolding(backendPayload);
            onHoldingAdded(); // Call parent callback to refresh portfolio
            onClose(); // Close modal
            setFormData({ // Reset form
                symbol: '', quantity: 0, purchase_price: 0, 
                purchase_date: new Date().toISOString().split('T')[0]
            });
        } catch (err: any) {
            setError(err.response?.data?.detail || err.message || "Failed to add holding.");
        } finally {
            setLoading(false);
        }
    };

    if (!isOpen) return null;

    return (
        <div style={modalOverlayStyle}>
            <div style={modalContentStyle}>
                <h3>Add New Holding</h3>
                {error && <p style={{ color: 'red' }}>{error}</p>}
                <form onSubmit={handleSubmit}>
                    <div style={formGroupStyle}>
                        <label htmlFor="symbol">Asset Symbol:</label>
                        <input type="text" id="symbol" name="symbol" value={formData.symbol} onChange={handleChange} required style={inputStyle} />
                    </div>
                    <div style={formGroupStyle}>
                        <label htmlFor="quantity">Quantity:</label>
                        <input type="number" id="quantity" name="quantity" value={formData.quantity} onChange={handleChange} step="any" required style={inputStyle} />
                    </div>
                    <div style={formGroupStyle}>
                        <label htmlFor="purchase_price">Purchase Price (per unit):</label>
                        <input type="number" id="purchase_price" name="purchase_price" value={formData.purchase_price} onChange={handleChange} step="any" required style={inputStyle} />
                    </div>
                    <div style={formGroupStyle}>
                        <label htmlFor="purchase_date">Purchase Date:</label>
                        <input type="date" id="purchase_date" name="purchase_date" value={formData.purchase_date} onChange={handleChange} required style={inputStyle} />
                    </div>
                    <button type="submit" disabled={loading} style={buttonStyle}>
                        {loading ? 'Adding...' : 'Add Holding'}
                    </button>
                    <button type="button" onClick={onClose} style={{...buttonStyle, backgroundColor: '#ccc', marginLeft: '10px'}}>
                        Cancel
                    </button>
                </form>
            </div>
        </div>
    );
};

// Basic Modal Styles
const modalOverlayStyle: React.CSSProperties = { position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, backgroundColor: 'rgba(0,0,0,0.5)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000 };
const modalContentStyle: React.CSSProperties = { background: 'white', padding: '20px', borderRadius: '5px', minWidth: '300px', boxShadow: '0 2px 10px rgba(0,0,0,0.1)' };
const formGroupStyle: React.CSSProperties = { marginBottom: '15px' };
const inputStyle: React.CSSProperties = { width: 'calc(100% - 10px)', padding: '8px', marginTop: '5px', border: '1px solid #ccc', borderRadius: '4px' };
const buttonStyle: React.CSSProperties = { padding: '10px 15px', border: 'none', borderRadius: '4px', cursor: 'pointer', backgroundColor: '#007bff', color: 'white' };

export default AddHoldingForm;
