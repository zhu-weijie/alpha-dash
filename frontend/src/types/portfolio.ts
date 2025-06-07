// src/types/portfolio.ts
import { Asset } from './asset';

export interface PortfolioHolding {
    id: number;
    user_id: number;
    asset_id: number;
    quantity: number;
    purchase_price: number;
    purchase_date: string;
    created_at: string;
    asset_info?: Asset | null;

    current_price?: number | null;
    current_value?: number | null;
    gain_loss?: number | null;
    gain_loss_percent?: number | null;
}

export interface PortfolioSummary {
    total_purchase_value: number;
    total_current_value: number;
    total_gain_loss: number;
    total_gain_loss_percent?: number | null;
    holdings: PortfolioHolding[];
}
