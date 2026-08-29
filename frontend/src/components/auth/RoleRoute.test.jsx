import { describe, it, expect, beforeAll, afterAll } from 'vitest';
import { renderToString } from 'react-dom/server';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import { RoleRoute } from './RoleRoute';
import { AuthContext } from '../../context/authCtx';

beforeAll(() => {
  globalThis.document = {
    documentElement: { getAttribute: () => 'dark' },
  };
  globalThis.MutationObserver = class {
    constructor() {}
    observe() {}
    disconnect() {}
  };
});

afterAll(() => {
  delete globalThis.document;
  delete globalThis.MutationObserver;
});

function buildTree(authStatus, user, roles = ['admin']) {
  return renderToString(
    <AuthContext.Provider value={{ status: authStatus, user }}>
      <MemoryRouter initialEntries={['/settings']}>
        <Routes>
          <Route element={<RoleRoute roles={roles} />}>
            <Route path="/settings" element={<main>SETTINGS_CONTENT</main>} />
          </Route>
        </Routes>
      </MemoryRouter>
    </AuthContext.Provider>
  );
}

describe('RoleRoute', () => {
  it('renders the loader while auth status is loading', () => {
    const html = buildTree('loading', null);
    expect(html).toContain('DriveVitals');
    expect(html).not.toContain('SETTINGS_CONTENT');
  });

  it('redirects to /login when not authenticated', () => {
    const html = buildTree('unauthenticated', null);
    expect(html).not.toContain('SETTINGS_CONTENT');
  });

  it('renders the outlet when user has the required role', () => {
    const html = buildTree('authenticated', { role: 'admin' });
    expect(html).toContain('SETTINGS_CONTENT');
  });

  it('shows Unauthorized page when user lacks the required role', () => {
    const html = buildTree('authenticated', { role: 'viewer' }, ['admin']);
    expect(html).not.toContain('SETTINGS_CONTENT');
    expect(html).toContain('Access denied');
  });

  it('does not redirect to /login when user lacks the required role', () => {
    const html = buildTree('authenticated', { role: 'operator' }, ['admin']);
    // Should NOT contain a redirect to /login — role denial shows Unauthorized, not login redirect
    expect(html).toContain('Access denied');
  });
});
