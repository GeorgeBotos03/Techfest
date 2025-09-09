import { ComponentFixture, TestBed } from '@angular/core/testing';

import { FinalConfirmation } from './final-confirmation';

describe('FinalConfirmation', () => {
  let component: FinalConfirmation;
  let fixture: ComponentFixture<FinalConfirmation>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [FinalConfirmation]
    })
    .compileComponents();

    fixture = TestBed.createComponent(FinalConfirmation);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
