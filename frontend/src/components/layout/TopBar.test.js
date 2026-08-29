import { describe, it, expect } from 'vitest';
import { getInitials, getRoleLabel } from '../../utils/identity';

describe('getInitials', () => {
  it('builds initials from first and last name', () => {
    expect(getInitials('John Doe')).toBe('JD');
    expect(getInitials('Ada Lovelace')).toBe('AL');
  });

  it('uses the first two characters for a single name', () => {
    expect(getInitials('Cher')).toBe('CH');
  });

  it('handles missing or blank names', () => {
    expect(getInitials(null)).toBe('DV');
    expect(getInitials('')).toBe('DV');
    expect(getInitials('   ')).toBe('DV');
  });

  it('handles extra whitespace and casing', () => {
    expect(getInitials('  john   doe  ')).toBe('JD');
    expect(getInitials('jonathan d. reid')).toBe('JR');
  });
});

describe('getRoleLabel', () => {
  it('maps canonical roles to friendly labels', () => {
    expect(getRoleLabel('admin')).toBe('Fleet Admin');
    expect(getRoleLabel('operator')).toBe('Fleet Operator');
    expect(getRoleLabel('viewer')).toBe('Viewer');
  });

  it('falls back for unknown roles', () => {
    expect(getRoleLabel('bogus')).toBe('Team Member');
    expect(getRoleLabel(null)).toBe('Team Member');
    expect(getRoleLabel(undefined)).toBe('Team Member');
  });
});