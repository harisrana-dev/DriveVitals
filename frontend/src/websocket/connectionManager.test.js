import { describe, it, expect } from 'vitest';
import { WS_AUTH_REJECT_CODE } from './connectionManager';

describe('connectionManager M2 constants', () => {
  it('exports WS_AUTH_REJECT_CODE as 4401', () => {
    expect(WS_AUTH_REJECT_CODE).toBe(4401);
  });

  it('4401 is in the reserved application range (4000–4999)', () => {
    expect(WS_AUTH_REJECT_CODE).toBeGreaterThanOrEqual(4000);
    expect(WS_AUTH_REJECT_CODE).toBeLessThanOrEqual(4999);
  });
});
