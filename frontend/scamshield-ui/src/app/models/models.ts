export type RiskLevel = 'low' | 'medium' | 'high';


export interface TransactionDetails {
fromAccount: string;
toRecipient: string; // name or business
iban?: string;
amount: number;
currency: string;
date: string; // ISO
reference?: string;
type: 'internal' | 'external' | 'online' | 'vendor';
device?: string;
location?: string;
}


export interface RiskReason { icon: string; title: string; desc?: string; }


export interface RiskAssessment {
overall: RiskLevel;
scorePct?: number; // 0..100 for pie/number
reasons: RiskReason[];
bars?: { name: string; value: number; }[]; // for Enhanced Verification
}


export interface RecipientIntel {
name: string; cui?: string; address?: string; incorporated?: string; reputation?: 'unverified'|'verified'|'blacklisted';
previousTx?: number;
flags?: string[];
}


export interface UserPatternSummary {
typicalAvg: number; largest: number; current: number; history: number[]; // for mini chart
}


export interface ChecklistItem { key: string; label: string; checked: boolean; }