import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';

export type ScoreReq = {
    ts: string;
    src_account_iban: string;
    dst_account_iban: string;
    amount: number;
    currency: string;
    channel: 'web' | 'mobile' | 'branch';
    is_first_to_payee: boolean;
    description?: string | null;
};

@Injectable({ providedIn: 'root' })
export class ApiService {
    private base = 'http://localhost:8000';
    constructor(private http: HttpClient) { }

    scorePayment(body: ScoreReq) {
        return this.http.post<{
            risk_score: number;
            action: string;
            reasons: string[];
            cooloff_minutes: number;
        }>(`${this.base}/scorePayment`, body);
    }

    listAlerts() {
        return this.http.get<
            Array<{
                id: number;
                ts: string;
                src_account_iban?: string;
                dst_account_iban?: string;
                amount: number;
                currency: string;
                channel: string;
                action: string;
                reasons: string[];
            }>
        >(`${this.base}/alerts`);
    }

    decideAlert(alertId: number, decision: 'release' | 'cancel') {
        const params = new URLSearchParams({ decision }).toString();
        return this.http.post<{ ok: boolean; id: number; new_action: string }>(
            `${this.base}/alerts/${alertId}/decision?${params}`,
            {}
        );
    }
}
