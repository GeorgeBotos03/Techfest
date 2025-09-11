import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

@Injectable({ providedIn: 'root' })
export class ApiService {
  private http = inject(HttpClient);

  // Schimbă baza dacă vrei să folosești absolut (fără proxy Angular).
  // Dacă ai proxy.conf.json setat, poți lăsa base = '' și apelurile vor fi relative.
  private base = 'http://localhost:8000';

  // === Transactions / scoring ===
  scoreTransaction(payload: any): Observable<any> {
    return this.http.post(`${this.base}/scorePayment`, payload);
  }

  // === Alerts ===
  getAlerts(): Observable<any> {
    return this.http.get(`${this.base}/alerts`);
  }

  decideAlert(alertId: number, decision: 'release' | 'cancel'): Observable<any> {
    return this.http.post(`${this.base}/alerts/${alertId}/decision?decision=${decision}`, {});
  }

  exportAlertsCsv(): Observable<Blob> {
    return this.http.get(`${this.base}/alerts/export.csv`, { responseType: 'blob' });
  }

  // === Stats ===
  getStats(): Observable<any> {
    return this.http.get(`${this.base}/stats`);
  }

  // === Watchlist ===
  getWatchlist(): Observable<any> {
    return this.http.get(`${this.base}/watchlist`);
  }

  addToWatchlist(iban: string): Observable<any> {
    return this.http.post(`${this.base}/watchlist/add?iban=${iban}`, {});
  }

  removeFromWatchlist(iban: string): Observable<any> {
    return this.http.post(`${this.base}/watchlist/remove?iban=${iban}`, {});
  }

  // === AI endpoints ===
  aiExplain(payload: any): Observable<{ summary: string; key_reasons: string[]; recommendations: string[] }> {
    return this.http.post<{ summary: string; key_reasons: string[]; recommendations: string[] }>(
      `${this.base}/ai/explain`,
      payload
    );
  }

  aiQuiz(payload: any): Observable<{ questions: string[]; rubric: string[] }> {
    return this.http.post<{ questions: string[]; rubric: string[] }>(
      `${this.base}/ai/quiz`,
      payload
    );
  }

  aiQuizScore(payload: any): Observable<{ score: number; decision: string; reasons: string[] }> {
    return this.http.post<{ score: number; decision: string; reasons: string[] }>(
      `${this.base}/ai/quiz/score`,
      payload
    );
  }

  aiClassify(payload: any): Observable<{ classification: string; confidence?: number; explanation?: string }> {
    return this.http.post<{ classification: string; confidence?: number; explanation?: string }>(
      `${this.base}/ai/classify`,
      payload
    );
  }
}
