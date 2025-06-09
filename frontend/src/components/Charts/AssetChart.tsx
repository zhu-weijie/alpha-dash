// src/components/Charts/AssetChart.tsx
import React from 'react';
import { Line } from 'react-chartjs-2';
import {
    Chart as ChartJS, CategoryScale, LinearScale, PointElement, LineElement,
    Title, Tooltip, Legend, TimeScale
} from 'chart.js';
import 'chartjs-adapter-date-fns';
import { HistoricalPricePoint } from '../../types/marketData';

ChartJS.register(
    CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend, TimeScale
);

interface AssetChartProps {
    data: HistoricalPricePoint[];
    assetSymbol?: string;
}

const AssetChart: React.FC<AssetChartProps> = ({ data, assetSymbol }) => {
    if (!data || data.length === 0) {
        return <p>No historical data available to display chart.</p>;
    }

    const chartData = {
        labels: data.map(point => point.date),
        datasets: [
            {
                label: `${assetSymbol || 'Asset'} Closing Price`,
                data: data.map(point => point.close),
                borderColor: 'rgb(75, 192, 192)',
                tension: 0.1,
                yAxisID: 'y',
            },
            ...(data.some(p => p.sma20 != null) ? [{
                label: 'SMA 20',
                data: data.map(point => point.sma20),
                borderColor: 'rgb(255, 159, 64)',
                borderWidth: 2,
                pointRadius: 0,
                tension: 0.1,
                yAxisID: 'y',
            }] : []),
            ...(data.some(p => p.sma50 != null) ? [{
                label: 'SMA 50',
                data: data.map(point => point.sma50),
                borderColor: 'rgb(255, 99, 132)',
                borderWidth: 2,
                pointRadius: 0,
                tension: 0.1,
                yAxisID: 'y',
            }] : []),
        ],
    };

    const options = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                position: 'top' as const,
            },
            title: {
                display: true,
                text: `${assetSymbol || 'Asset'} Price Chart`
            }
        },
        scales: {
            x: {
                type: 'time' as const,
                time: {
                    unit: 'day' as const,
                    displayFormats: {
                        day: 'MMM D, YYYY'
                    }
                },
                title: { display: true, text: 'Date' }
            },
            y: {
                type: 'linear' as const, 
                display: true,
                position: 'left' as const,
                title: { display: true, text: 'Price (USD)' }
            }
        }
    };

    return <div style={{ height: '400px', width: '100%' }}><Line options={options} data={chartData} /></div>;
};

export default AssetChart;
