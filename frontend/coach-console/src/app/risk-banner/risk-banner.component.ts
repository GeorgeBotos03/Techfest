import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-risk-banner',
  standalone: true,
  imports: [CommonModule],
  template: `
  <div [ngStyle]="{padding:'12px', borderRadius:'12px', marginTop:'12px',
                   background: result.action==='hold' ? '#ffe5e5' :
                               result.action==='warn' ? '#fff8e1' : '#e7ffe5',
                   border: '1px solid #ccc'}">
    <h3 style="margin:0 0 8px 0;">Action: {{result.action | uppercase}}</h3>
    <div *ngIf="result.cooloff_minutes">Cool-off: {{result.cooloff_minutes}} min</div>
    <ul>
      <li *ngFor="let r of result.reasons">{{r}}</li>
    </ul>
  </div>
  `
})
export class RiskBannerComponent {
  @Input() result!: { action: string; reasons: string[]; risk_score: number; cooloff_minutes: number };
}
