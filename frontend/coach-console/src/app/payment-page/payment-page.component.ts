import { Component } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators, FormGroup } from '@angular/forms';
import { ApiService } from '../api.service';
import { CommonModule } from '@angular/common';
import { RiskBannerComponent } from '../risk-banner/risk-banner.component';

@Component({
    selector: 'app-payment-page',
    standalone: true,
    imports: [CommonModule, ReactiveFormsModule, RiskBannerComponent],
    templateUrl: './payment-page.component.html',
})
export class PaymentPageComponent {
    result: { action: string; reasons: string[]; risk_score: number; cooloff_minutes: number } | null = null;

    form: FormGroup;

    constructor(private fb: FormBuilder, private api: ApiService) {
        this.form = this.fb.group({
            src: ['RO12BANK0000000000000001', [Validators.required]],
            dst: ['RO49AAAA1B31007593840000', [Validators.required]],
            amount: [120, [Validators.required, Validators.min(1)]],
            channel: ['web', [Validators.required]],
            first: [false],
            payee: ['Acme SRL'],
        });
    }

    submit() {
        const v = this.form.value;
        this.result = null;
        this.api.scorePayment({
            ts: new Date().toISOString(),
            src_account_iban: v['src'],
            dst_account_iban: v['dst'],
            amount: Number(v['amount']),
            currency: 'RON',
            channel: v['channel'] as any,
            is_first_to_payee: !!v['first'],
            description: v['payee'] ? `payee: ${v['payee']}` : null
        }).subscribe(res => this.result = res);
    }
}
