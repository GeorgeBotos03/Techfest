import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';

import { assessment, checklist } from '../../../models/mock-data';
import { RiskChip } from '../../../ui/risk-chip/risk-chip';
import { RiskBars } from '../../../ui/risk-bars/risk-bars';

@Component({
  selector: 'app-educational-checkpoint',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    RouterLink,
    RiskChip,
    RiskBars
  ],
  templateUrl: './educational-checkpoint.html', // convenție Angular
  styleUrls: ['./educational-checkpoint.scss']  // dacă ai fișier de stil
})
export class EducationalCheckpoint {
  score = assessment.scorePct ?? 65;
  items = checklist;

  allChecked() {
    return this.items.every(i => i.checked);
  }
}
