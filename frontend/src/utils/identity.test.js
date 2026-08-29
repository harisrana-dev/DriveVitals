import { describe, it, expect } from 'vitest';
import {
  hasRole,
  hasAnyRole,
  isAdmin,
  isOperator,
  isViewer,
  canAccessSettings,
  getInitials,
  getRoleLabel,
} from './identity';

describe('hasRole', () => {
  it('returns true when user has the specified role', () => {
    expect(hasRole({ role: 'admin' }, 'admin')).toBe(true);
  });

  it('returns false when user has a different role', () => {
    expect(hasRole({ role: 'viewer' }, 'admin')).toBe(false);
  });

  it('returns false for null user', () => {
    expect(hasRole(null, 'admin')).toBe(false);
  });

  it('returns false for undefined user', () => {
    expect(hasRole(undefined, 'admin')).toBe(false);
  });
});

describe('hasAnyRole', () => {
  it('returns true when user role is in the allowed list', () => {
    expect(hasAnyRole({ role: 'operator' }, ['admin', 'operator'])).toBe(true);
  });

  it('returns false when user role is not in the allowed list', () => {
    expect(hasAnyRole({ role: 'viewer' }, ['admin', 'operator'])).toBe(false);
  });

  it('returns false for null user', () => {
    expect(hasAnyRole(null, ['admin'])).toBe(false);
  });

  it('returns false when roles is not an array', () => {
    expect(hasAnyRole({ role: 'admin' }, 'admin')).toBe(false);
  });
});

describe('isAdmin', () => {
  it('returns true for admin users', () => {
    expect(isAdmin({ role: 'admin' })).toBe(true);
  });

  it('returns false for non-admin users', () => {
    expect(isAdmin({ role: 'operator' })).toBe(false);
    expect(isAdmin({ role: 'viewer' })).toBe(false);
  });

  it('returns false for null user', () => {
    expect(isAdmin(null)).toBe(false);
  });
});

describe('isOperator', () => {
  it('returns true for operator users', () => {
    expect(isOperator({ role: 'operator' })).toBe(true);
  });

  it('returns false for non-operator users', () => {
    expect(isOperator({ role: 'admin' })).toBe(false);
    expect(isOperator({ role: 'viewer' })).toBe(false);
  });
});

describe('isViewer', () => {
  it('returns true for viewer users', () => {
    expect(isViewer({ role: 'viewer' })).toBe(true);
  });

  it('returns false for non-viewer users', () => {
    expect(isViewer({ role: 'admin' })).toBe(false);
    expect(isViewer({ role: 'operator' })).toBe(false);
  });
});

describe('canAccessSettings', () => {
  it('returns true only for admin users', () => {
    expect(canAccessSettings({ role: 'admin' })).toBe(true);
  });

  it('returns false for operator users', () => {
    expect(canAccessSettings({ role: 'operator' })).toBe(false);
  });

  it('returns false for viewer users', () => {
    expect(canAccessSettings({ role: 'viewer' })).toBe(false);
  });

  it('returns false for null user', () => {
    expect(canAccessSettings(null)).toBe(false);
  });
});

describe('getInitials (existing)', () => {
  it('builds initials from first and last name', () => {
    expect(getInitials('John Doe')).toBe('JD');
  });
});

describe('getRoleLabel (existing)', () => {
  it('maps canonical roles to friendly labels', () => {
    expect(getRoleLabel('admin')).toBe('Fleet Admin');
    expect(getRoleLabel('operator')).toBe('Fleet Operator');
    expect(getRoleLabel('viewer')).toBe('Viewer');
  });
});
