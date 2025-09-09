import { Component } from '@angular/core';
import { assessment, tx } from '../../../models/mock-data';
import { RiskBars } from '../../../ui/risk-bars/risk-bars';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { RiskChip } from '../../../ui/risk-chip/risk-chip';


@Component({
  selector: 'app-enhanced-verification',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink, RiskChip],
  templateUrl: './enhanced-verification.html'
})

export class EnhancedVerification {
  tx = tx; bars = assessment.bars ?? [];
  delay = 24;
  method: 'qa' | 'sms' | 'email' | 'video' = 'qa';
}
