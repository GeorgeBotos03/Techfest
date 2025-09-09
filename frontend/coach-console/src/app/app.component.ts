import { Component } from '@angular/core';
import { RouterOutlet } from '@angular/router';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [RouterOutlet],
  template: `
    <nav style="display:flex; gap:12px; padding:12px; border-bottom:1px solid #ddd">
      <a routerLink="/pay">Coach</a>
      <a routerLink="/alerts">Console</a>
    </nav>
    <router-outlet />
  `,
})
export class AppComponent { }
