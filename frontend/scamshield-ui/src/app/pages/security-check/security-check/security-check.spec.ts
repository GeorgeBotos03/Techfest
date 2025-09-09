import { ComponentFixture, TestBed } from '@angular/core/testing';

import { SecurityCheck } from './security-check';

describe('SecurityCheck', () => {
  let component: SecurityCheck;
  let fixture: ComponentFixture<SecurityCheck>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [SecurityCheck]
    })
    .compileComponents();

    fixture = TestBed.createComponent(SecurityCheck);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
