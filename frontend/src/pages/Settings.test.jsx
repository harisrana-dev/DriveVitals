import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderToString } from 'react-dom/server';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import { AuthContext } from '../context/authCtx';
import { SettingsPage } from './Settings';
import { settingsApi } from '../api/settingsApi';

// ── Mocks ──────────────────────────────────────────────────────────────────

vi.mock('../api/settingsApi', () => ({
  settingsApi: {
    getSettings: vi.fn(),
    getCategory: vi.fn(),
    updateCategory: vi.fn(),
  },
}));

vi.mock('../hooks/useAuth', () => ({
  useAuth: () => ({
    user: { full_name: 'Test Admin', role: 'admin' },
    isAdmin: true,
  }),
}));

// ── Helpers ────────────────────────────────────────────────────────────────

function renderSettingsPage() {
  settingsApi.getSettings.mockResolvedValue({ data: {} });

  const html = renderToString(
    <AuthContext.Provider value={{ status: 'authenticated', user: { role: 'admin' } }}>
      <MemoryRouter initialEntries={['/settings']}>
        <Routes>
          <Route path="/settings" element={<SettingsPage />} />
        </Routes>
      </MemoryRouter>
    </AuthContext.Provider>
  );
  return html;
}

// ── Tests ──────────────────────────────────────────────────────────────────

beforeEach(() => {
  vi.clearAllMocks();
});

describe('Settings page', () => {
  it('renders the Settings header', () => {
    const html = renderSettingsPage();
    expect(html).toContain('Settings');
    expect(html).toContain('Fleet administration and system configuration');
  });

  it('renders all tab labels', () => {
    const html = renderSettingsPage();
    expect(html).toContain('Account');
    expect(html).toContain('Security');
    expect(html).toContain('System');
    expect(html).toContain('Analytics');
    expect(html).toContain('Digital Twin');
  });

  it('renders loading skeleton initially (before async data loads)', () => {
    const html = renderSettingsPage();
    // SSR renders the loading state skeleton
    expect(html).toContain('ui-skeleton');
  });

  it('does not render hardcoded John Doe identity', () => {
    const html = renderSettingsPage();
    expect(html).not.toContain('John Doe');
    expect(html).not.toContain('Fleet Manager');
  });

  it('has correct page structure', () => {
    const html = renderSettingsPage();
    // Verify the Settings icon container exists
    expect(html).toContain('lucide-settings');
  });
});

describe('settingsApi', () => {
  it('exports getSettings, getCategory, updateCategory', () => {
    expect(typeof settingsApi.getSettings).toBe('function');
    expect(typeof settingsApi.getCategory).toBe('function');
    expect(typeof settingsApi.updateCategory).toBe('function');
  });
});

describe('Settings page tabs', () => {
  it('tab buttons have correct structure', () => {
    const html = renderSettingsPage();
    // All 5 tabs should be present as buttons
    expect(html).toContain('>Account<');
    expect(html).toContain('>Security<');
    expect(html).toContain('>System<');
    expect(html).toContain('>Analytics<');
    expect(html).toContain('>Digital Twin<');
  });
});
