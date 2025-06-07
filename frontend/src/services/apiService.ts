// src/services/apiService.ts
import axios from 'axios';
import { PortfolioSummary } from '../types/portfolio';

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

// export const loginUser = async (credentials) => { ... store token in localStorage ... }
