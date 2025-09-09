// src/app/pages/security-check/security-check/security-check.component.ts
import { Component, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { ApiService } from '../../../data/api.service';

// UI
import { RiskChip } from '../../../ui/risk-chip/risk-chip';
import { MiniLineChart } from '../../../ui/mini-line-chart/mini-line-chart';

type VM = {
  tx: any;
  recipient: any;
  pattern: any;
  assessment: {
    level?: string;
    overall?: number | string;
    reasons: Array<{ title?: string; desc?: string }>;
  };
};

@Component({
  selector: 'app-security-check',
  standalone: true,
  imports: [CommonModule, RouterLink, RiskChip, MiniLineChart],
  templateUrl: './security-check.html'
})
export class SecurityCheck {
  private api = inject(ApiService);

  loading = signal(true);
  error   = signal<string | null>(null);

  private _vm = signal<VM>({
    tx: {},
    recipient: {},
    pattern: {},
    assessment: { level: 'unknown', overall: 0, reasons: [] }
  });

  ngOnInit() {
    // === PAYLOAD FLAT cu câmpurile cerute (din 422):
    // ts, channel, src_account_iban, dst_account_iban
    const nowEpoch = Math.floor(Date.now() / 1000);

    const payload: any = {
      ts: nowEpoch,                          // dacă modelul vrea ISO -> new Date().toISOString()
      channel: 'web',                        // web | mobile | api (alege ce ai în backend)
      src_account_iban: 'RO49AAAA1B31007593840000',
      dst_account_iban: 'RO49AAAA1B31007593840000',

      // restul câmpurilor (de obicei acceptate ca opționale)
      amount:   2450,
      currency: 'USD',
      reference:'Software Services',
      tx_type:  'vendor',                    // dacă modelul tău e 'type', schimbă în 'type'
      device:   'Chrome on Windows',
      location: 'Bucharest, RO',

      // identitate destinatar (dacă backendul le ignoră, nu deranjează)
      to_name:  'Global Tech Solutions Ltd.',
      to_cui:   'HRB 112233',

      // module (snake_case dacă așa e în /docs)
      features: {
        rules: true,
        text_signals: true,
        velocity: true,
        cop: true,
        watchlist: true
      }
    };

    this.api.scoreTransaction(payload).subscribe({
      next: (res: any) => {
        const assessment = {
          level:   res?.risk?.level ?? res?.assessment?.level ?? 'unknown',
          overall: res?.risk?.scorePct ?? res?.assessment?.overall ?? res?.score ?? 0,
          reasons: (res?.risk?.reasons ?? res?.assessment?.reasons ?? res?.reasons ?? [])
            .map((r: any) => ({ title: r?.title, desc: r?.desc ?? r?.description ?? '' }))
        };

        this._vm.set({
          // reconstruim view modelul din payload (dacă API nu returnează tx complet)
          tx: {
            fromAccount: payload.src_account_iban,
            toRecipient: payload.to_name || payload.dst_account_iban,
            amount: payload.amount,
            currency: payload.currency,
            reference: payload.reference,
            type: payload.tx_type || payload.type,
            date: new Date(
              typeof payload.ts === 'number' ? payload.ts * 1000 : Date.parse(payload.ts)
            ).toISOString(),
            device: payload.device,
            location: payload.location
          },
          recipient: res?.recipient ?? {
            name: payload.to_name || '(IBAN) ' + payload.dst_account_iban,
            cui:  payload.to_cui || '',
            reputation: 'unverified'
          },
          pattern:   res?.pattern ?? {},
          assessment
        });
        this.loading.set(false);
      },
      error: (e) => {
        // afișăm clar ce câmpuri lipsesc
        const detail = (e?.error?.detail ?? []) as Array<any>;
        if (Array.isArray(detail) && detail.length) {
          console.table(detail.map(x => ({
            field: Array.isArray(x.loc) ? x.loc.slice(1).join('.') : (x.loc ?? ''),
            msg: x.msg
          })));
          this.error.set(
            detail.map(x => `${Array.isArray(x.loc) ? x.loc.slice(1).join('.') : x.loc}: ${x.msg}`).join('\n')
          );
        } else {
          this.error.set(e?.message || 'Request failed');
        }
        this.loading.set(false);
      }
    });
  }

  // === getters pentru template ===
  get tx()         { return this._vm().tx; }
  get recipient()  { return this._vm().recipient; }
  get pattern()    { return this._vm().pattern; }
  get assessment() { return this._vm().assessment; }

  // === garantăm tipul cerut de <risk-chip> ===
  get riskLevel(): 'low' | 'medium' | 'high' {
    const lvl = (this._vm().assessment.level || '').toLowerCase();
    if (lvl.includes('low')) return 'low';
    if (lvl.includes('med')) return 'medium';
    if (lvl.includes('high')) return 'high';
    const score = Number(this._vm().assessment.overall) || 0;
    if (score >= 75) return 'high';
    if (score >= 40) return 'medium';
    return 'low';
  }
}
