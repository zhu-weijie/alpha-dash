// src/components/Portfolio/HoldingForm.tsx
import React, { useState, useEffect } from 'react';
import { PortfolioHoldingCreatePayload, BackendPortfolioHoldingCreate, PortfolioHoldingUpdatePayload } from '../../types/portfolio';
import { Asset } from '../../types/asset';
import { getAssetBySymbol } from '../../services/apiService';


interface HoldingFormProps {
    isOpen: boolean;
    onClose: () => void;
    onSubmitForm: (data: BackendPortfolioHoldingCreate | PortfolioHoldingUpdatePayload) => Promise<void>;
    initialData?: PortfolioHoldingCreatePayload | PortfolioHoldingUpdatePayload;
    mode: 'add' | 'edit';
    assetSymbolReadOnly?: string;
}

const HoldingForm: React.FC<HoldingFormProps> = ({ 
    isOpen, onClose, onSubmitForm, initialData, mode, assetSymbolReadOnly 
}) => {
    const [formData, setFormData] = useState(
        initialData || { quantity: 0, purchase_price: 0, purchase_date: new Date().toISOString().split('T')[0] }
    );
    const [error, setError] = useState<string | null>(null);
    const [loading, setLoading] = useState<boolean>(false);

    useEffect(() => {
        if (initialData) {
            const formattedData = { ...initialData };
            if (initialData.purchase_date) {
                formattedData.purchase_date = new Date(initialData.purchase_date).toISOString().split('T')[0];
            }
            setFormData(fd => ({...fd, ...formattedData}));
        } else {
             setFormData({ quantity: 0, purchase_price: 0, purchase_date: new Date().toISOString().split('T')[0] });
        }
    }, [isOpen, initialData]);

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

        const currentSymbol = mode === 'edit' && assetSymbolReadOnly ? assetSymbolReadOnly : (formData as PortfolioHoldingCreatePayload).symbol;

        if (mode === 'add' && !currentSymbol) {
            setError("Asset Symbol is required for adding a new holding.");
            setLoading(false);
            return;
        }
        if (formData.quantity && formData.purchase_price && (formData.quantity <= 0 || formData.purchase_price < 0)) {
            setError("Quantity must be > 0 and Purchase Price must be >= 0.");
            setLoading(false);
            return;
        }

        try {
            let submitData: BackendPortfolioHoldingCreate | PortfolioHoldingUpdatePayload;

            if (mode === 'add') {
                const asset: Asset | null = await getAssetBySymbol(currentSymbol);
                if (!asset) {
                    setError(`Asset with symbol "${currentSymbol}" not found.`);
                    setLoading(false);
                    return;
                }
                submitData = {
                    asset_id: asset.id,
                    quantity: formData.quantity,
                    purchase_price: formData.purchase_price,
                    purchase_date: new Date(formData.purchase_date + "T00:00:00.000Z").toISOString(),
                };
            } else {
                submitData = {
                    quantity: formData.quantity,
                    purchase_price: formData.purchase_price,
                    purchase_date: new Date(formData.purchase_date + "T00:00:00.000Z").toISOString(),
                };
            }
            await onSubmitForm(submitData);
            onClose();
        } catch (err: any) {
            setError(err.response?.data?.detail || err.message || `Failed to ${mode} holding.`);
        } finally {
            setLoading(false);
        }
    };
    
    if (!isOpen) return null;

    return (
        <div>
            <div>
                <h3>{mode === 'add' ? 'Add New' : 'Edit'} Holding {assetSymbolReadOnly ? `(${assetSymbolReadOnly})` : ''}</h3>
                {error && <p style={{ color: 'red' }}>{error}</p>}
                <form onSubmit={handleSubmit}>
                    {mode === 'add' && (
                        <div>
                            <label htmlFor="symbol">Asset Symbol:</label>
                            <input type="text" id="symbol" name="symbol" value={(formData as PortfolioHoldingCreatePayload).symbol} onChange={handleChange} required />
                        </div>
                    )}
                    <div> <label htmlFor="quantity">Quantity:</label> <input type="number" id="quantity" name="quantity" value={formData.quantity} onChange={handleChange} step="any" required /> </div>
                    <div> <label htmlFor="purchase_price">Purchase Price:</label> <input type="number" id="purchase_price" name="purchase_price" value={formData.purchase_price} onChange={handleChange} step="any" required /> </div>
                    <div> <label htmlFor="purchase_date">Purchase Date:</label> <input type="date" id="purchase_date" name="purchase_date" value={formData.purchase_date} onChange={handleChange} required /> </div>
                    <button type="submit" disabled={loading}> {loading ? 'Saving...' : (mode === 'add' ? 'Add' : 'Update')} Holding </button>
                    <button type="button" onClick={onClose}> Cancel </button>
                </form>
            </div>
        </div>
    );
};

export default HoldingForm;
