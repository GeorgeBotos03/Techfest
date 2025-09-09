import { Component } from '@angular/core';
import { assessment, checklist } from '../../../models/mock-data';
// Update the import path to the correct location of RiskChip
import { RiskChip } from '../../../ui/risk-chip/risk-chip';


@Component({
  selector: 'app-educational-checkpoint',
  standalone: true,
  imports: [RiskChip],
  templateUrl: './educational-checkpoint.html'
})
export class EducationalCheckpoint {
  score = assessment.scorePct ?? 65;
  items = checklist;
  allChecked() { return this.items.every(i => i.checked); }
}

