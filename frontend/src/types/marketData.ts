// src/types/marketData.ts
export interface HistoricalPricePoint {
    date: string;
    open: number;
    high: number;
    low: number;
    close: number;
    volume: number;
}

export interface HistoricalPricePoint {
    date: string;
    open: number;
    high: number;
    low: number;
    close: number;
    volume: number;
    sma20?: number | null;
    sma50?: number | null;
}
