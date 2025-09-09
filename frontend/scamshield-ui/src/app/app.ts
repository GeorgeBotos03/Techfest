import { Component, signal } from '@angular/core';
import { RouterLink, RouterOutlet } from '@angular/router';

@Component({
  selector: 'app-root',
  standalone: true,
   imports: [RouterOutlet, RouterLink],
  template: `
 <main class="main">
      <div class="container">
        <header style="display:flex;align-items:center;justify-content:space-between;margin-bottom:16px;">
          <h1 style="margin:0;font-size:22px;">ScamShield</h1>
          <nav style="display:flex;gap:8px;">
            <a class="btn ghost" routerLink="/security-check">Security Check</a>
            <a class="btn ghost" routerLink="/educational">Educational</a>
            <a class="btn ghost" routerLink="/enhanced">Enhanced Verification</a>
            <a class="btn primary" routerLink="/final">Final</a>
          </nav>
        </header>
        <router-outlet/>
      </div>
    </main>
  `
})
export class App {
  protected readonly title = signal('scamshield-ui');
}
