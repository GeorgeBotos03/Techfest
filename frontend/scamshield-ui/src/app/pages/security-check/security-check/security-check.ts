import { Component } from '@angular/core';
import { assessment, pattern, recipient, tx } from '../../../models/mock-data';
import { RiskChip } from '../../../ui/risk-chip/risk-chip';
import { MiniLineChart } from '../../../ui/mini-line-chart/mini-line-chart';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';

@Component({
  selector: 'app-security-check',
  standalone: true,
  imports: [RiskChip, MiniLineChart, CommonModule, RouterLink],
  templateUrl: './security-check.html'
})

export class SecurityCheck {
  tx = tx; recipient = recipient; assessment = assessment; pattern = pattern;
}
