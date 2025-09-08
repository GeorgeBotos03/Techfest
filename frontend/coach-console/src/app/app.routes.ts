import { Routes } from '@angular/router';
import { PaymentPageComponent } from './payment-page/payment-page.component';
import { AlertsPageComponent } from './alerts-page/alerts-page.component';

export const routes: Routes = [
    { path: '', redirectTo: 'pay', pathMatch: 'full' },
    { path: 'pay', component: PaymentPageComponent },
    { path: 'alerts', component: AlertsPageComponent },
];
