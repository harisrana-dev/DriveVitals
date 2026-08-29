import { describe, it, expect, beforeAll, afterAll } from 'vitest';
import { renderToString } from 'react-dom/server';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import { ProtectedRoute } from './ProtectedRoute';
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

function buildTree(status) {
  return renderToString(
    <AuthContext.Provider value={{ status }}>
      <MemoryRouter initialEntries={['/app']}>
        <Routes>
          <Route element={<ProtectedRoute />}>
            <Route path="/app" element={<main>PROTECTED_CONTENT</main>} />
          </Route>
        </Routes>
      </MemoryRouter>
    </AuthContext.Provider>
  );
}

describe('ProtectedRoute', () => {
  it('renders the loader while auth status is loading', () => {
    const html = buildTree('loading');
    expect(html).toContain('DriveVitals');
    expect(html).not.toContain('PROTECTED_CONTENT');
  });

  it('renders nothing protected when the user is not authenticated', () => {
    const html = buildTree('unauthenticated');
    expect(html).not.toContain('PROTECTED_CONTENT');
  });

  it('renders the protected outlet when the user is authenticated', () => {
    const html = buildTree('authenticated');
    expect(html).toContain('PROTECTED_CONTENT');
    expect(html).not.toContain('Establishing telemetry link');
  });
});