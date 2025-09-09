import { ComponentFixture, TestBed } from '@angular/core/testing';

import { EnhancedVerification } from './enhanced-verification';

describe('EnhancedVerification', () => {
  let component: EnhancedVerification;
  let fixture: ComponentFixture<EnhancedVerification>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [EnhancedVerification]
    })
    .compileComponents();

    fixture = TestBed.createComponent(EnhancedVerification);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
