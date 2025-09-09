import { ComponentFixture, TestBed } from '@angular/core/testing';

import { EducationalCheckpoint } from './educational-checkpoint';

describe('EducationalCheckpoint', () => {
  let component: EducationalCheckpoint;
  let fixture: ComponentFixture<EducationalCheckpoint>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [EducationalCheckpoint]
    })
    .compileComponents();

    fixture = TestBed.createComponent(EducationalCheckpoint);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
