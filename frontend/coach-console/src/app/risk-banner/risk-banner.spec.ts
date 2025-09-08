import { ComponentFixture, TestBed } from '@angular/core/testing';

import { RiskBanner } from './risk-banner';

describe('RiskBanner', () => {
  let component: RiskBanner;
  let fixture: ComponentFixture<RiskBanner>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [RiskBanner]
    })
    .compileComponents();

    fixture = TestBed.createComponent(RiskBanner);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
