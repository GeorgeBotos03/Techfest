import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterLink, Router } from '@angular/router';
import { RiskChip } from '../../../ui/risk-chip/risk-chip';
import { TransactionStateService } from '../../../data/transaction-state.service';

@Component({
  selector: 'app-final-confirmation',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink, RiskChip],
  templateUrl: './final-confirmation.html'
})
export class FinalConfirmation {
  private router = inject(Router);
  private state = inject(TransactionStateService);

  tx = this.state.getTransaction();
  assessment = this.state.getAssessment();
  level = (this.assessment?.level ?? 'medium');
  confirmed = false;

  ngOnInit() {
    if (!this.state.hasTransaction()) {
      this.router.navigate(['/security-check']);
    }
  }
}
