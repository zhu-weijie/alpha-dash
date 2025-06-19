// src/components/Portfolio/__tests__/HoldingForm.test.tsx
import React from 'react';
import { render, screen } from '@testing-library/react';
import HoldingForm from '../HoldingForm';

jest.mock('../../../services/apiService', () => ({
    getAssetBySymbol: jest.fn().mockResolvedValue(null),
}));

describe('HoldingForm', () => {
    const mockOnClose = jest.fn();
    const mockOnSubmitForm = jest.fn();

    test('renders in "add" mode with all fields', () => {
        render(
            <HoldingForm 
                isOpen={true} 
                onClose={mockOnClose} 
                onSubmitForm={mockOnSubmitForm} 
                mode="add" 
            />
        );

        expect(screen.getByLabelText(/Asset Symbol/i)).toBeInTheDocument();
        expect(screen.getByLabelText(/Quantity/i)).toBeInTheDocument();
        expect(screen.getByLabelText(/Purchase Price/i)).toBeInTheDocument();
        expect(screen.getByLabelText(/Purchase Date/i)).toBeInTheDocument();
        expect(screen.getByRole('button', { name: /Add Holding/i })).toBeInTheDocument();
    });

    test('renders in "edit" mode with symbol displayed (not as input) and correct button text', () => {
        const initialData = {
            quantity: 10,
            purchase_price: 100,
            purchase_date: "2023-01-01",
        };
        const readOnlySymbol = "AAPL";

        render(
            <HoldingForm 
                isOpen={true} 
                onClose={mockOnClose} 
                onSubmitForm={mockOnSubmitForm} 
                initialData={initialData}
                mode="edit"
                assetSymbolReadOnly={readOnlySymbol}
            />
        );

        expect(screen.getByRole('heading', { name: new RegExp(`Edit Holding \\(${readOnlySymbol}\\)`, 'i') })).toBeInTheDocument();
        
        const quantityInput = screen.getByLabelText(/Quantity/i) as HTMLInputElement;
        expect(quantityInput.value).toBe("10");

        const priceInput = screen.getByLabelText(/Purchase Price/i) as HTMLInputElement;
        expect(priceInput.value).toBe("100");
        
        const dateInput = screen.getByLabelText(/Purchase Date/i) as HTMLInputElement;
        expect(dateInput.value).toBe("2023-01-01");
        
        expect(screen.queryByLabelText(/Asset Symbol/i)).not.toBeInTheDocument();
        
        expect(screen.getByRole('button', { name: /Update Holding/i })).toBeInTheDocument();
    });
});
