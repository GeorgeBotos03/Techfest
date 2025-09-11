import { Routes } from '@angular/router';
import { SecurityCheck } from './pages/security-check/security-check/security-check';
import { EducationalCheckpoint } from './pages/educational-checkpoint/educational-checkpoint/educational-checkpoint';
import { EnhancedVerification } from './pages/enhanced-verification/enhanced-verification/enhanced-verification';
import { FinalConfirmation } from './pages/final-confirmation/final-confirmation/final-confirmation';

export const routes: Routes = [
    { path: '', redirectTo: 'security-check', pathMatch: 'full' },
    { path: 'security-check', component: SecurityCheck },
    { path: 'educational-checkpoint', component: EducationalCheckpoint },
    { path: 'enhanced-verification', component: EnhancedVerification },
    { path: 'final-confirmation', component: FinalConfirmation },
    { path: '**', redirectTo: 'security-check' },
];
