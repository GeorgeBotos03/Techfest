// src/app/data/chat-stub.ts
import { Injectable } from '@angular/core';
import { delay, of, Observable } from 'rxjs';

@Injectable({ providedIn: 'root' })
export class ChatStub {
  // Simulează un răspuns de la “assistant”
  replyTo(prompt: string): Observable<string> {
    const canned =
      prompt.toLowerCase().includes('fraud')
        ? 'Invoice fraud e des întâlnit. Vrei o verificare rapidă a destinatarului sau tips de confirmare?'
        : 'Am notat. Pot explica riscul tranzacției, pași de verificare sau să-ți pregătesc un checklist.';
    return of(canned).pipe(delay(800));
  }
}
