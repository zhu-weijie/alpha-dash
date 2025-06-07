// src/components/Charts/AssetChart.tsx
import React from 'react';
import { Line } from 'react-chartjs-2';
import {
    Chart as ChartJS,
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    Title,
    Tooltip,
    Legend,
    TimeScale,
    TimeSeriesScale
} from 'chart.js';
import 'chartjs-adapter-date-fns';
import { HistoricalPricePoint } from '../../types/marketData';

ChartJS.register(
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    Title,
    Tooltip,
    Legend,
    TimeScale // Register TimeScale
    // TimeSeriesScale // Register if using time series scale explicitly
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
        labels: data.map(point => point.date), // Dates for x-axis
        datasets: [
            {
                label: `${assetSymbol || 'Asset'} Closing Price`,
                data: data.map(point => point.close),
                borderColor: 'rgb(75, 192, 192)',
                tension: 0.1,
            },
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
                text: `${assetSymbol || 'Asset'} Historical Price`,
            },
        },
        scales: {
            x: {
                type: 'time' as const, // Use time scale
                time: {
                    unit: 'day' as const, // Display unit
                    tooltipFormat: 'MMM dd, yyyy' as const, // e.g., Oct 28, 2023
                    displayFormats: {
                        day: 'MMM dd' as const // How dates are displayed on the axis
                    }
                },
                title: {
                    display: true,
                    text: 'Date'
                }
            },
            y: {
                title: {
                    display: true,
                    text: 'Price (USD)' // Assuming USD
                }
            }
        }
    };

    return <div style={{ height: '400px', width: '100%' }}><Line options={options} data={chartData} /></div>;
};

export default AssetChart;
