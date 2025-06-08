// src/types/asset.ts
export enum AssetType {
    STOCK = "stock",
    CRYPTO = "crypto",
}

export interface Asset {
    id: number;
    symbol: string;
    name?: string | null;
    asset_type: AssetType;
    created_at: string;
}

export interface AssetCreatePayload {
    symbol: string;
    name: string;
    asset_type: AssetType;
}
