import { ComponentFixture, TestBed } from '@angular/core/testing';

import { RiskBars } from './risk-bars';

describe('RiskBars', () => {
  let component: RiskBars;
  let fixture: ComponentFixture<RiskBars>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [RiskBars]
    })
    .compileComponents();

    fixture = TestBed.createComponent(RiskBars);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
