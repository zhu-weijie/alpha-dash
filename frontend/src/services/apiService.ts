// src/services/apiService.ts
import axios from 'axios';
import { PortfolioSummary, PortfolioHolding, BackendPortfolioHoldingCreate, PortfolioHoldingUpdatePayload } from '../types/portfolio';
import { HistoricalPricePoint } from '../types/marketData';
import { Asset, AssetCreatePayload } from '../types/asset';
import { UserAssetSummaryItem } from '../types/userSummary';
import { notifyError } from '../utils/notifications';

const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000/api/v1';

const getAuthHeaders = () => {
    const token = localStorage.getItem('authToken');
    if (token) {
        return { Authorization: `Bearer ${token}` };
    }
    return {};
};

export const getPortfolioSummary = async (): Promise<PortfolioSummary> => {
    try {
        const response = await axios.get<PortfolioSummary>(
            `${API_BASE_URL}/portfolio/holdings/`,
            { headers: getAuthHeaders() }
        );
        return response.data;
    } catch (error: any) {
        const errorMessage = error.response?.data?.detail || 
                             (error.isAxiosError && error.message === 'Network Error' ? 'Network Error: Could not connect to server.' : error.message) ||
                             "An unexpected error occurred fetching portfolio.";
        console.error("Error fetching portfolio summary:", error);
        notifyError(errorMessage);
            
        if (axios.isAxiosError(error) && error.response?.status === 401) {
            window.location.href = '/login';
        }
        throw error;
    }
};

export const getAssetHistoricalData = async (
    symbol: string,
    outputsize: 'compact' | 'full' = 'compact'
): Promise<HistoricalPricePoint[]> => {
    try {
        const response = await axios.get<HistoricalPricePoint[]>(
            `${API_BASE_URL}/market-data/${symbol}/history?outputsize=${outputsize}`,
        );
        return response.data;
    } catch (error: any) {
        const errorMessage = error.response?.data?.detail ||
                             (error.isAxiosError && error.message === 'Network Error' ? `Network Error fetching history for ${symbol}.` : error.message) ||
                             `Failed to fetch historical data for ${symbol}.`;
        console.error(`Error fetching historical data for ${symbol}:`, error);
        notifyError(errorMessage);
        throw error;
    }
};

export const getAssetBySymbol = async (symbol: string): Promise<Asset | null> => {
    try {
        const response = await axios.get<Asset[]>(
            `${API_BASE_URL}/assets/?symbol=${symbol.toUpperCase()}`,
            { headers: getAuthHeaders() }
        );
        if (response.data && response.data.length > 0) {
            return response.data[0];
        }
        return null;
    } catch (error: any) {
        if (axios.isAxiosError(error) && error.response?.status === 404) {
            console.warn(`Asset with symbol ${symbol} not found (404).`);
            return null;
        }
        
        const errorMessage = error.response?.data?.detail ||
                             (error.isAxiosError && error.message === 'Network Error' ? `Network Error fetching asset ${symbol}.` : error.message) ||
                             `Failed to fetch asset ${symbol}.`;
        console.error(`Error fetching asset by symbol ${symbol}:`, error);
        notifyError(errorMessage);
        throw error;
    }
};

export const addPortfolioHolding = async (
    holdingData: BackendPortfolioHoldingCreate
): Promise<PortfolioHolding> => {
    try {
        const response = await axios.post<PortfolioHolding>(
            `${API_BASE_URL}/portfolio/holdings/`,
            holdingData,
            { headers: getAuthHeaders() }
        );
        return response.data;
    } catch (error: any) {
        const errorMessage = error.response?.data?.detail ||
                             (error.isAxiosError && error.message === 'Network Error' ? 'Network Error: Could not add holding.' : error.message) ||
                             "Failed to add portfolio holding.";
        console.error("Error adding portfolio holding:", error);
        notifyError(errorMessage);
        throw error;
    }
};

export const createAsset = async (
    assetData: AssetCreatePayload
): Promise<Asset> => {
    try {
        const response = await axios.post<Asset>(
            `${API_BASE_URL}/assets/`,
            assetData,
            { headers: getAuthHeaders() }
        );
        return response.data;
    } catch (error: any) {
        const errorMessage = error.response?.data?.detail ||
                             (error.isAxiosError && error.message === 'Network Error' ? 'Network Error: Could not create asset.' : error.message) ||
                             "Failed to create asset.";
        console.error("Error creating asset:", error);
        notifyError(errorMessage);
        throw error;
    }
};

export const updatePortfolioHolding = async (
    holdingId: number,
    holdingData: PortfolioHoldingUpdatePayload
): Promise<PortfolioHolding> => {
    try {
        const response = await axios.put<PortfolioHolding>(
            `${API_BASE_URL}/portfolio/holdings/${holdingId}`,
            holdingData,
            { headers: getAuthHeaders() }
        );
        return response.data;
    } catch (error: any) {
        const errorMessage = error.response?.data?.detail ||
                             (error.isAxiosError && error.message === 'Network Error' ? `Network Error updating holding ${holdingId}.` : error.message) ||
                             `Failed to update portfolio holding ${holdingId}.`;
        console.error(`Error updating portfolio holding ${holdingId}:`, error);
        notifyError(errorMessage);
        throw error;
    }
};

export const deletePortfolioHolding = async (holdingId: number): Promise<void | PortfolioHolding> => {
    try {
        const response = await axios.delete<PortfolioHolding>(
            `${API_BASE_URL}/portfolio/holdings/${holdingId}`,
            { headers: getAuthHeaders() }
        );
        return response.data;
    } catch (error: any) {
        const errorMessage = error.response?.data?.detail ||
                             (error.isAxiosError && error.message === 'Network Error' ? `Network Error deleting holding ${holdingId}.` : error.message) ||
                             `Failed to delete portfolio holding ${holdingId}.`;
        console.error(`Error deleting portfolio holding ${holdingId}:`, error);
        notifyError(errorMessage);
        throw error;
    }
};

export const getUserAssetSummary = async (): Promise<UserAssetSummaryItem[]> => {
    try {
        const response = await axios.get<UserAssetSummaryItem[]>(
            `${API_BASE_URL}/users/me/asset-summary`,
            { headers: getAuthHeaders() }
        );
        return response.data;
    } catch (error) {
        console.error("Error fetching user asset summary:", error);
        if (axios.isAxiosError(error) && error.response?.status === 401) {
            window.location.href = '/login';
        }
        throw error;
    }
};
