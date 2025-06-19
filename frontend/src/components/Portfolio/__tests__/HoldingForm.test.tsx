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
});