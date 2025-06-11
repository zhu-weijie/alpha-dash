// src/components/Portfolio/HoldingForm.tsx
import React, { useState, useEffect } from 'react';
import { PortfolioHoldingCreatePayload, BackendPortfolioHoldingCreate, PortfolioHoldingUpdatePayload } from '../../types/portfolio';
import { Asset } from '../../types/asset';
import { getAssetBySymbol } from '../../services/apiService';
import Spinner from '../Common/Spinner';
import { notifySuccess } from '../../utils/notifications';


interface HoldingFormProps {
    isOpen: boolean;
    onClose: () => void;
    onSubmitForm: (data: BackendPortfolioHoldingCreate | PortfolioHoldingUpdatePayload) => Promise<void>;
    initialData?: PortfolioHoldingCreatePayload | PortfolioHoldingUpdatePayload;
    mode: 'add' | 'edit';
    assetSymbolReadOnly?: string;
}

type FormDataType = {
    symbol?: string;
    quantity: number;
    purchase_price: number;
    purchase_date: string;
};

const HoldingForm: React.FC<HoldingFormProps> = ({ 
    isOpen, onClose, onSubmitForm, initialData, mode, assetSymbolReadOnly 
}) => {
    const [formData, setFormData] = useState<FormDataType>({
        symbol: '',
        quantity: 0,
        purchase_price: 0,
        purchase_date: new Date().toISOString().split('T')[0],
    });
    const [error, setError] = useState<string | null>(null);
    const [loading, setLoading] = useState<boolean>(false);

    useEffect(() => {
        if (isOpen) {
            if (mode === 'edit' && initialData) {
                const formattedInitialData: Partial<FormDataType> = {};
                if (initialData.quantity !== undefined) formattedInitialData.quantity = initialData.quantity;
                if (initialData.purchase_price !== undefined) formattedInitialData.purchase_price = initialData.purchase_price;
                if (initialData.purchase_date) {
                    try {
                        formattedInitialData.purchase_date = new Date(initialData.purchase_date).toISOString().split('T')[0];
                    } catch (e) {
                        console.error("Error formatting initial purchase date for form:", e);
                        formattedInitialData.purchase_date = new Date().toISOString().split('T')[0];
                    }
                }
                
                setFormData({
                    symbol: assetSymbolReadOnly || '',
                    quantity: 0,
                    purchase_price: 0,
                    purchase_date: new Date().toISOString().split('T')[0],
                    ...formattedInitialData
                });
            } else if (mode === 'add') {
                setFormData({ 
                    symbol: '',
                    quantity: 0, 
                    purchase_price: 0, 
                    purchase_date: new Date().toISOString().split('T')[0] 
                });
            }
        }
    }, [isOpen, initialData, mode, assetSymbolReadOnly]);

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

        let symbolToLookup: string | undefined;
        if (mode === 'edit') {
            symbolToLookup = assetSymbolReadOnly;
        } else {
            symbolToLookup = formData.symbol;
        }
    
        if (mode === 'add' && (!symbolToLookup || symbolToLookup.trim() === '')) {
            setError("Asset Symbol is required for adding a new holding.");
            setLoading(false);
            return;
        }

        try {
            let submitData: BackendPortfolioHoldingCreate | PortfolioHoldingUpdatePayload;

            let finalPurchaseDateISO: string;
            if (formData.purchase_date) {
                const localDateParts = formData.purchase_date.split('-').map(Number);
                const utcDate = new Date(Date.UTC(localDateParts[0], localDateParts[1] - 1, localDateParts[2]));
                finalPurchaseDateISO = utcDate.toISOString();
            } else {
                setError("Purchase date is invalid.");
                setLoading(false);
                return;
            }

            if (mode === 'add') {
                if (!symbolToLookup) { return; }
                const asset: Asset | null = await getAssetBySymbol(symbolToLookup);
                if (!asset) {
                    setError(`Asset with symbol "${currentSymbol}" not found.`);
                    setLoading(false);
                    return;
                }
                submitData = {
                    asset_id: asset.id,
                    quantity: formData.quantity,
                    purchase_price: formData.purchase_price,
                    purchase_date: finalPurchaseDateISO,
                };
            } else {
                submitData = {
                    quantity: formData.quantity,
                    purchase_price: formData.purchase_price,
                    purchase_date: finalPurchaseDateISO,
                };
            }
            await onSubmitForm(submitData);
            notifySuccess(`Holding ${mode === 'add' ? 'added' : 'updated'} successfully!`);
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
                    <button type="submit" disabled={loading} style={buttonStyle}>
                            {loading ? (
                                <>
                                    <Spinner size={20} color="white" inline={true} /> 
                                    Saving... 
                                </>
                            ) : (
                                (mode === 'add' ? 'Add' : 'Update') + ' Holding'
                            )}
                        </button>
                    <button type="button" onClick={onClose}> Cancel </button>
                </form>
            </div>
        </div>
    );
};

const buttonStyle: React.CSSProperties = { padding: '10px 15px', border: 'none', borderRadius: '4px', cursor: 'pointer', backgroundColor: '#007bff', color: 'white' };

export default HoldingForm;
