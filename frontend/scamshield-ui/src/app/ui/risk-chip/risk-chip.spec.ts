import { ComponentFixture, TestBed } from '@angular/core/testing';

import { RiskChip } from './risk-chip';

describe('RiskChip', () => {
  let component: RiskChip;
  let fixture: ComponentFixture<RiskChip>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [RiskChip]
    })
    .compileComponents();

    fixture = TestBed.createComponent(RiskChip);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
