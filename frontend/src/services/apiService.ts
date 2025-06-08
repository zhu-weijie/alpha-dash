// src/services/apiService.ts
import axios from 'axios';
import { PortfolioSummary, PortfolioHolding, BackendPortfolioHoldingCreate } from '../types/portfolio';
import { HistoricalPricePoint } from '../types/marketData';
import { Asset, AssetCreatePayload } from '../types/asset';

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
    } catch (error) {
        console.error("Error fetching portfolio summary:", error);
        if (axios.isAxiosError(error) && error.response?.status === 401) {
            // Handle unauthorized, e.g., redirect to login
            // window.location.href = '/login';
        }
        throw error; // Re-throw to be caught by the component
    }
};

export const getAssetHistoricalData = async (
    symbol: string,
    outputsize: 'compact' | 'full' = 'compact'
): Promise<HistoricalPricePoint[]> => {
    try {
        const response = await axios.get<HistoricalPricePoint[]>(
            `${API_BASE_URL}/market-data/${symbol}/history?outputsize=${outputsize}`,
            // { headers: getAuthHeaders() }
        );
        return response.data;
    } catch (error) {
        console.error(`Error fetching historical data for ${symbol}:`, error);
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
    } catch (error) {
        console.error(`Error fetching asset by symbol ${symbol}:`, error);
        if (axios.isAxiosError(error) && error.response?.status === 404) {
            return null;
        }
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
    } catch (error) {
        console.error("Error adding portfolio holding:", error);
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
    } catch (error) {
        console.error("Error creating asset:", error);
        throw error;
    }
};
