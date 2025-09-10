import { Component, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ChatStub } from '../../../data/chat-stub';

type Msg = { role: 'user' | 'assistant'; text: string; ts: number };

@Component({
  selector: 'chat-widget',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './chat-widget.html',
  styleUrls: ['./chat-widget.scss'],
})
export class ChatWidget {
  open = signal(false);
  input = signal('');
  msgs = signal<Msg[]>([
    {
      role: 'assistant',
      text:
        '👋 Salut! Sunt ScamShield Assistant. Întreabă-mă orice despre tranzacții și riscuri.',
      ts: Date.now(),
    },
  ]);
  sending = signal(false);

  constructor(private stub: ChatStub) {}

  toggle() {
    this.open.update((o) => !o);
  }

  // Accept Event to satisfy template typing; cast inside.
  onEnter(e: Event) {
    const k = e as KeyboardEvent;
    if (!k.shiftKey) {
      k.preventDefault();
      this.send();
    }
  }

  send() {
    const text = this.input().trim();
    if (!text) return;

    this.msgs.update((m) => [...m, { role: 'user', text, ts: Date.now() }]);
    this.input.set('');
    this.sending.set(true);

    this.stub.replyTo(text).subscribe({
      next: (ans: string) => {
        this.msgs.update((m) => [
          ...m,
          { role: 'assistant', text: String(ans), ts: Date.now() },
        ]);
        this.sending.set(false);
      },
      error: () => {
        this.msgs.update((m) => [
          ...m,
          { role: 'assistant', text: '⚠️ Eroare la răspuns.', ts: Date.now() },
        ]);
        this.sending.set(false);
      },
    });
  }
}
