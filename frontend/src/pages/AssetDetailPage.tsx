// src/pages/AssetDetailPage.tsx
import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { getAssetHistoricalData } from '../services/apiService';
import { HistoricalPricePoint } from '../types/marketData';
import AssetChart from '../components/Charts/AssetChart';
import Spinner from '../components/Common/Spinner';

const AssetDetailPage: React.FC = () => {
    const params = useParams<{ symbol?: string }>();
    const symbol = params?.symbol;
    const [historicalData, setHistoricalData] = useState<HistoricalPricePoint[] | null>(null);
    const [loading, setLoading] = useState<boolean>(true);
    const [error, setError] = useState<string | null>(null);
    const [outputSize, setOutputSize] = useState<'compact' | 'full'>('compact');


    useEffect(() => {
        if (!symbol) {
            setLoading(false);
            return;
        }

        const fetchData = async () => {
            try {
                setLoading(true);
                setError(null);
                const data = await getAssetHistoricalData(symbol, outputSize);
                setHistoricalData(data);
            } catch (err: any) {
                setError(err.message || `Failed to fetch historical data for ${symbol}.`);
            } finally {
                setLoading(false);
            }
        };

        fetchData();
    }, [symbol, outputSize]);

    if (!symbol) return <p>No asset symbol specified.</p>;
    if (loading) {
        return (
            <div style={{ display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center', minHeight: '200px' }}>
                <Spinner size={60} />
                <p>Loading chart data for {symbol}...</p>
            </div>
        );
    }
    if (error) return <p style={{ color: 'red' }}>Error: {error}</p>;
    if (!historicalData || historicalData.length === 0) return <p>No historical data found for {symbol}.</p>;

    return (
        <div>
            <h2>Historical Prices for {symbol.toUpperCase()}</h2>
            <div>
                <label htmlFor="outputsize">Data Range: </label>
                <select 
                    id="outputsize" 
                    value={outputSize} 
                    onChange={(e) => setOutputSize(e.target.value as 'compact' | 'full')}
                >
                    <option value="compact">Compact (100 days)</option>
                    <option value="full">Full History</option>
                </select>
            </div>
            <AssetChart data={historicalData} assetSymbol={symbol.toUpperCase()} />
        </div>
    );
};

export default AssetDetailPage;
