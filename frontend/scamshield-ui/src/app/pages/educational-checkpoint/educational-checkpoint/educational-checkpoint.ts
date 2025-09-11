import { Component, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { ApiService } from '../../../data/api.service';
import { TransactionStateService } from '../../../data/transaction-state.service';

type Assessment = {
  overall?: number; scorePct?: number;
  level?: 'low' | 'medium' | 'high' | 'unknown';
  reasons?: string[];
};

@Component({
  selector: 'app-educational-checkpoint',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink],
  templateUrl: './educational-checkpoint.html',
  styleUrls: ['./educational-checkpoint.scss'],
})
export class EducationalCheckpoint {
  private router = inject(Router);
  private api = inject(ApiService);
  private state = inject(TransactionStateService);

  score = 65; // fallback
  tx = this.state.getTransaction();
  assessment = this.state.getAssessment();
  aiExplain = this.state.getAiExplain();
  aiClass = this.state.getAiClass();

  // quiz
  quizQuestions = signal<string[]>([]);
  quizRubric = signal<string[]>([]);
  quizScore = signal<number>(0);
  quizDecision = signal<string>('');
  quizReasons = signal<string[]>([]);

  ngOnInit() {
    if (!this.state.hasTransaction()) {
      this.router.navigate(['/security-check']); return;
    }
    const a = this.state.getAssessment() as Assessment | null;
    this.score = Number(a?.overall ?? a?.scorePct ?? 65);
  }

  startQuiz(signals: any) {
    this.api.aiQuiz({ signals }).subscribe({
      next: (r: any) => { this.quizQuestions.set(r.questions ?? []); this.quizRubric.set(r.rubric ?? []); }
    });
  }
  scoreQuiz(answers: string[]) {
    this.api.aiQuizScore({ questions: this.quizQuestions(), answers }).subscribe({
      next: (r: any) => {
        this.quizScore.set(r.score ?? 0);
        this.quizDecision.set(r.decision ?? '');
        this.quizReasons.set(r.reasons ?? []);
      }
    });
  }

  goEnhanced() { this.router.navigate(['/enhanced-verification']); }
}
