import { describe, it, expect } from 'vitest';
import { renderToString } from 'react-dom/server';
import { MemoryRouter } from 'react-router-dom';
import { Unauthorized } from './Unauthorized';

function renderUnauthorized() {
  return renderToString(
    <MemoryRouter>
      <Unauthorized />
    </MemoryRouter>
  );
}

describe('Unauthorized', () => {
  it('renders the access denied heading', () => {
    const html = renderUnauthorized();
    expect(html).toContain('Access denied');
  });

  it('renders a message about contacting the administrator', () => {
    const html = renderUnauthorized();
    expect(html).toContain('contact your fleet administrator');
  });

  it('renders a back to dashboard link', () => {
    const html = renderUnauthorized();
    expect(html).toContain('Back to dashboard');
  });
});
