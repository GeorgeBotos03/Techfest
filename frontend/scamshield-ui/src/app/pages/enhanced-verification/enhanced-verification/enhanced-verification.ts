import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { TransactionStateService } from '../../../data/transaction-state.service';
import { RiskBars } from '../../../ui/risk-bars/risk-bars';

@Component({
  selector: 'app-enhanced-verification',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink, RiskBars],
  templateUrl: './enhanced-verification.html',
  styleUrls: ['./enhanced-verification.scss']
})
export class EnhancedVerification {
  private router = inject(Router);
  private state = inject(TransactionStateService);

  tx = this.state.getTransaction();
  assessment = this.state.getAssessment();
  aiExplain = this.state.getAiExplain();
  aiClass = this.state.getAiClass();

  delay = 24;
  method: 'qa' | 'sms' | 'email' | 'video' = 'qa';

  ngOnInit() {
    if (!this.state.hasTransaction()) {
      this.router.navigate(['/security-check']);
    }
  }
}
