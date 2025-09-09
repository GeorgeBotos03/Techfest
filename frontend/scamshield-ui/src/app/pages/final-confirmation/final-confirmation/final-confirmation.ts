import { Component } from '@angular/core';
import { assessment, tx } from '../../../models/mock-data';
import { RiskChip } from '../../../ui/risk-chip/risk-chip';
import { FormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';

@Component({
  selector: 'app-final-confirmation',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink, RiskChip],
  templateUrl: './final-confirmation.html'
})

export class FinalConfirmation {
  tx = tx; reasons = assessment.reasons; level = 'medium' as const;
  confirmed = false;
}
