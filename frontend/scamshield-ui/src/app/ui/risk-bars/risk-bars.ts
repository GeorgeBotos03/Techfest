import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';

type Bar = { name: string; value: number };

@Component({
  selector: 'risk-bars',
  standalone: true,
  imports: [CommonModule],
  template: `
<div class="bars" *ngIf="data?.length; else noBars">
  <div class="bar" *ngFor="let b of data">
    <div class="name">{{ b.name }}</div>
    <div class="track">
      <div class="fill" [style.width.%]="clamp(b.value)"></div>
    </div>
    <div class="val">{{ clamp(b.value) | number:'1.0-0' }}%</div>
  </div>
</div>
<ng-template #noBars>
  <div class="help">No bar data available.</div>
</ng-template>
`,
  styles: [`
.bars { display:grid; gap:8px; }
.bar { display:grid; grid-template-columns: 140px 1fr 48px; align-items:center; gap:8px; }
.name { color: var(--muted); font-size: 13px; }
.track { height: 10px; background: #0a1118; border: 1px solid var(--border); border-radius: 6px; overflow: hidden; }
.fill { height: 100%; background: linear-gradient(90deg, var(--brand), #6ad1ff); }
.val { text-align: right; font-size: 12px; color: var(--muted); }
`]
})
export class RiskBars {
  @Input() data: Bar[] = [];
  clamp(v: number) { v = Number(v) || 0; return Math.max(0, Math.min(100, v)); }
}
