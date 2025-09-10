import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

@Injectable({ providedIn: 'root' })
export class ApiService {
  private http = inject(HttpClient);
  private base = 'http://localhost:8000';   // baza pentru backend-ul tău FastAPI

  scoreTransaction(payload: any): Observable<any> {
    return this.http.post(`${this.base}/scorePayment`, payload);
  }

  getAssessment(txId: string) {
    return this.http.get(`${this.base}/transactions/${txId}/assessment`);
  }

  startVerification(body: { txId: string; method: string }) {
    return this.http.post(`${this.base}/verification/start`, body);
  }

  confirmVerification(body: any) {
    return this.http.post(`${this.base}/verification/confirm`, body);
  }

  scheduleCoolingOff(body: { txId: string; hours: number }) {
    return this.http.post(`${this.base}/cooling-off/schedule`, body);
  }

  notifyTrustedContact(body: { txId: string; contactId: string }) {
    return this.http.post(`${this.base}/notify/trusted-contact`, body);
  }

  submitDecision(txId: string, body: any) {
    return this.http.post(`${this.base}/transactions/${txId}/decision`, body);
  }

  getStats() {
    return this.http.get(`${this.base}/stats/overview`);
  }

  getAlerts() {
    return this.http.get(`${this.base}/alerts`);
  }
  aiExplain(payload: any) { return this.http.post<any>(`${this.base}/ai/explain`, payload); }
  aiQuiz(payload: any) { return this.http.post<any>(`${this.base}/ai/quiz`, payload); }
  aiQuizScore(p: any) { return this.http.post<any>(`${this.base}/ai/quiz/score`, p); }
  aiClassify(p: any) { return this.http.post<any>(`${this.base}/ai/classify`, p); }
}



