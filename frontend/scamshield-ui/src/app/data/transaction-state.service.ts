import { Injectable } from '@angular/core';

type Assessment = {
    overall?: number;      // 0..100
    scorePct?: number;     // compat vechi
    level?: 'low' | 'medium' | 'high' | 'unknown';
    reasons?: string[];
};

type AiExplain = { summary: string; key_reasons: string[]; recommendations: string[] } | null;
type AiClass = string | null;

@Injectable({ providedIn: 'root' })
export class TransactionStateService {
    // --- TRANSACTION ---
    private tx: any = null;
    setTransaction(t: any) { this.tx = t; }
    getTransaction() { return this.tx; }
    hasTransaction() { return !!this.tx; }

    // --- ASSESSMENT (scor nivel/reasons) ---
    private assessment: Assessment | null = null;
    setAssessment(a: Assessment | null) { this.assessment = a; }
    getAssessment(): Assessment | null { return this.assessment; }

    // --- AI Explain (summary/reasons/reco) ---
    private aiExplain: AiExplain = null;
    setAiExplain(x: AiExplain) { this.aiExplain = x; }
    getAiExplain(): AiExplain { return this.aiExplain; }

    // --- AI Classify (badge) ---
    private aiClass: AiClass = null;
    setAiClass(x: AiClass) { this.aiClass = x; }
    getAiClass(): AiClass { return this.aiClass; }

    clear() {
        this.tx = null;
        this.assessment = null;
        this.aiExplain = null;
        this.aiClass = null;
    }
}
