import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RiskLevel } from '../../models/models';

@Component({
  selector: 'risk-chip',
  standalone: true,
  imports: [CommonModule],
  template: `
<span class="badge" [ngClass]="{ low: level==='low', med: level==='medium', high: level==='high' }">
  <ng-content></ng-content>
</span>
`
})
export class RiskChip {
  @Input() level: RiskLevel = 'low';
}
