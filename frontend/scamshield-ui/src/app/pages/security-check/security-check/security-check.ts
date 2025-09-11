import { Component, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router, RouterLink } from '@angular/router';
import { ApiService } from '../../../data/api.service';
import { TransactionStateService } from '../../../data/transaction-state.service';
import { RiskChip } from '../../../ui/risk-chip/risk-chip';
import { MiniLineChart } from '../../../ui/mini-line-chart/mini-line-chart';

type VM = {
  tx: any;
  recipient: any;
  pattern: any;
  assessment: {
    level?: 'low' | 'medium' | 'high' | 'unknown';
    overall?: number;
    reasons: Array<{ title?: string; desc?: string }>;
  };
};

type AIRiskResult = { summary: string; key_reasons: string[]; recommendations: string[] };

function randomTransaction() {
  const amounts = [2450, 120, 5000, 320, 780];
  const channels = ['web', 'mobile', 'branch'] as const;
  const descriptions = [
    'urgent crypto investment', 'invoice payment', 'family support', 'loan repayment', 'gift for friend'
  ];
  return {
    amount: amounts[Math.floor(Math.random() * amounts.length)],
    channel: channels[Math.floor(Math.random() * channels.length)],
    description: descriptions[Math.floor(Math.random() * descriptions.length)],
    src_account_iban: 'RO49AAAA1B31007593840000',
    dst_account_iban: 'RO49BBBB1B31007593840001',
    is_first_to_payee: Math.random() > 0.5,
    ts: new Date().toISOString(),
    currency: 'RON',
    device_fp: 'demo-device',
  };
}

@Component({
  selector: 'app-security-check',
  standalone: true,
  imports: [CommonModule, RouterLink, RiskChip, MiniLineChart],
  templateUrl: './security-check.html',
})
export class SecurityCheck {
  private api = inject(ApiService);
  private state = inject(TransactionStateService);
  private router = inject(Router);

  loading = signal(true);
  error = signal<string | null>(null);

  private _vm = signal<VM>({
    tx: {}, recipient: {}, pattern: {},
    assessment: { level: 'unknown', overall: 0, reasons: [] },
  });

  aiRiskResult = signal<AIRiskResult | null>(null);
  aiClassification = signal<string | null>(null);

  ngOnInit() { this.reloadTransaction(); }

  reloadTransaction() {
    this.loading.set(true); this.error.set(null);
    const payload = randomTransaction();

    this.api.scoreTransaction(payload).subscribe({
      next: (res: any) => {
        const assessment = {
          level: (res.level as VM['assessment']['level']) || 'unknown',
          overall: (res.score as number) || 0,
          reasons: (res.reasons || []).map((r: string) => ({ title: r, desc: '' })),
        };

        // 1) UI local
        this._vm.set({ tx: payload, recipient: {}, pattern: {}, assessment });
        this.loading.set(false);

        // 2) salvează în store pt. paginile următoare
        this.state.setTransaction(payload);
        this.state.setAssessment(assessment as any);

        const features = {
          amount: payload.amount, channel: payload.channel,
          description: payload.description,
          src_account_iban: payload.src_account_iban,
          dst_account_iban: payload.dst_account_iban,
        };
        const signals = {
          cop_ok: res.cop_ok ?? true,
          mule_score: res.mule_score ?? 0,
          watchlisted: res.watchlisted ?? false,
          ml_p: res.ml_p ?? 0,
        };

        // 3) AI Explain
        this.api.aiExplain({ features, signals }).subscribe({
          next: (aiRes: AIRiskResult) => {
            const cleaned = {
              summary: aiRes?.summary ?? 'No AI assessment available.',
              key_reasons: aiRes?.key_reasons ?? [],
              recommendations: aiRes?.recommendations ?? [],
            };
            this.aiRiskResult.set(cleaned);
            this.state.setAiExplain(cleaned);   // <-- salvat pt. celelalte pagini
          },
          error: () => {
            const fb = { summary: 'AI unavailable', key_reasons: [], recommendations: [] };
            this.aiRiskResult.set(fb);
            this.state.setAiExplain(fb);
          }
        });

        // 4) AI Classify
        this.api.aiClassify({ features, signals }).subscribe({
          next: (classRes: any) => {
            const c = classRes?.classification ?? null;
            this.aiClassification.set(c);
            this.state.setAiClass(c);           // <-- salvat pt. celelalte pagini
          },
          error: () => { this.aiClassification.set(null); this.state.setAiClass(null); }
        });
      },
      error: () => { this.error.set('Eroare la scor clasic'); this.loading.set(false); }
    });
  }

  // helpers pt. template
  get tx() { return this._vm().tx; }
  get assessment() { return this._vm().assessment; }
  get riskLevel(): 'low' | 'medium' | 'high' {
    const lvl = this.assessment.level;
    if (lvl === 'high') return 'high';
    if (lvl === 'medium') return 'medium';
    return 'low';
  }
  get aiSummary(): string { return this.aiRiskResult()?.summary ?? '—'; }

  // navigare
  goEducational() { this.router.navigate(['/educational-checkpoint']); }
  goEnhanced() { this.router.navigate(['/enhanced-verification']); }
}
