import { Routes } from '@angular/router';
import { SecurityCheck } from './pages/security-check/security-check/security-check';
import { EducationalCheckpoint } from './pages/educational-checkpoint/educational-checkpoint/educational-checkpoint';
import { EnhancedVerification } from './pages/enhanced-verification/enhanced-verification/enhanced-verification';
import { FinalConfirmation } from './pages/final-confirmation/final-confirmation/final-confirmation';


export const routes: Routes = [
{ path: '', pathMatch: 'full', redirectTo: 'security-check' },
{ path: 'security-check', component: SecurityCheck },
{ path: 'educational', component: EducationalCheckpoint },
{ path: 'enhanced', component: EnhancedVerification },
{ path: 'final', component: FinalConfirmation },
{ path: '**', redirectTo: 'security-check' }
];