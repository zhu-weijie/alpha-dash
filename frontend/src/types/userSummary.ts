// src/types/userSummary.ts (or portfolio.ts)
import { AssetType } from './asset';

export interface UserAssetSummaryItem {
    asset_id: number;
    symbol: string;
    name?: string | null;
    asset_type: AssetType;
    total_quantity: number;
    weighted_average_purchase_price: number;
}
