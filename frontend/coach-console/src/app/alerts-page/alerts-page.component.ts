import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ApiService } from '../api.service';

@Component({
  selector: 'app-alerts-page',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './alerts-page.component.html',
})
export class AlertsPageComponent implements OnInit {
  alerts: any[] = [];
  loading = false;

  constructor(private api: ApiService) { }

  ngOnInit() { this.refresh(); }

  refresh() {
    this.loading = true;
    this.api.listAlerts().subscribe(res => { this.alerts = res; this.loading = false; });
  }

  decide(a: any, decision: 'release' | 'cancel') {
    this.api.decideAlert(a.id, decision).subscribe(_ => this.refresh());
  }
}
