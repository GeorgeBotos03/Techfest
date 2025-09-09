import { ComponentFixture, TestBed } from '@angular/core/testing';

import { MiniLineChart } from './mini-line-chart';

describe('MiniLineChart', () => {
  let component: MiniLineChart;
  let fixture: ComponentFixture<MiniLineChart>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [MiniLineChart]
    })
    .compileComponents();

    fixture = TestBed.createComponent(MiniLineChart);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
