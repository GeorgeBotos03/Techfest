import { TestBed } from '@angular/core/testing';

import { ChatStub } from './chat-stub';

describe('ChatStub', () => {
  let service: ChatStub;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(ChatStub);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});
