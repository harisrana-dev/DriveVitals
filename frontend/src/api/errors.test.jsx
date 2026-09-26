import { describe, it, expect } from 'vitest';
import { renderToStaticMarkup } from 'react-dom/server';
import { ApiError, formatApiError, formatValidationDetail } from './errors';

// A verbatim FastAPI 422 body for a driver create missing `license_number`.
const FASTAPI_422 = {
  detail: [
    {
      type: 'missing',
      loc: ['body', 'license_number'],
      msg: 'Field required',
      input: { driver_id: 'd1', first_name: 'Ada', last_name: 'Lovelace' },
      url: 'https://errors.pydantic.dev/2.13/v/missing',
    },
  ],
};

const VEHICLE_422 = [
  { type: 'missing', loc: ['body', 'registration_number'], msg: 'Field required' },
  { type: 'missing', loc: ['body', 'vin'], msg: 'Field required' },
  { type: 'missing', loc: ['body', 'year'], msg: 'Field required' },
];

// Mirrors the notice banner in DigitalTwinLab: `<div>{notice}</div>`.
function renderNotice(notice) {
  return renderToStaticMarkup(<div>{notice}</div>);
}

describe('formatApiError', () => {
  it('turns a FastAPI 422 detail array into a readable field list', () => {
    const result = formatApiError(new ApiError(422, FASTAPI_422.detail));
    expect(result).toBe('license_number: Field required');
  });

  it('joins every missing field in a 422 body', () => {
    const result = formatApiError(new ApiError(422, VEHICLE_422));
    expect(result).toBe(
      'registration_number: Field required; vin: Field required; year: Field required'
    );
  });

  it('drops the body/query segment from the field path', () => {
    const result = formatApiError(
      new ApiError(422, [{ loc: ['query', 'assignment_ids'], msg: 'Field required' }])
    );
    expect(result).toBe('assignment_ids: Field required');
  });

  it('keeps nested field paths readable', () => {
    const result = formatApiError(
      new ApiError(422, [{ loc: ['body', 'vehicles', 0, 'vin'], msg: 'Field required' }])
    );
    expect(result).toBe('vehicles.0.vin: Field required');
  });

  it('passes through a plain string detail unchanged', () => {
    expect(formatApiError(new ApiError(404, 'Scenario x not found'))).toBe(
      'Scenario x not found'
    );
  });

  it('reads detail.message from a non-array object detail', () => {
    expect(formatApiError({ detail: { message: 'boom' } })).toBe('boom');
  });

  it('falls back to the error message when detail is unusable', () => {
    expect(formatApiError(new TypeError('Failed to fetch'))).toBe('Failed to fetch');
  });

  it('uses the caller fallback when there is nothing usable', () => {
    expect(formatApiError(null, 'Failed to create driver')).toBe('Failed to create driver');
    expect(formatApiError({}, 'Failed to create driver')).toBe('Failed to create driver');
  });

  it('always returns a string, never an object or array', () => {
    const hostile = [
      new ApiError(422, FASTAPI_422.detail),
      new ApiError(422, VEHICLE_422),
      new ApiError(500, { unexpected: 'shape' }),
      new ApiError(400, [null, 42, 'plain string entry']),
      { detail: [{ loc: [], msg: 'Whole-payload failure' }] },
      new Error(''),
      undefined,
    ];
    for (const error of hostile) {
      expect(typeof formatApiError(error, 'fallback')).toBe('string');
    }
  });
});

describe('formatValidationDetail', () => {
  it('returns null for a non-array detail', () => {
    expect(formatValidationDetail('nope')).toBeNull();
    expect(formatValidationDetail(undefined)).toBeNull();
  });

  it('returns null for an array with nothing usable in it', () => {
    expect(formatValidationDetail([null, undefined, 7])).toBeNull();
  });

  it('handles a validation error with no field path', () => {
    expect(formatValidationDetail([{ msg: 'Whole-payload failure' }])).toBe(
      'Whole-payload failure'
    );
  });
});

describe('notice rendering regression', () => {
  it('renders the formatted 422 message without throwing', () => {
    const notice = formatApiError(new ApiError(422, FASTAPI_422.detail), 'Failed');
    expect(() => renderNotice(notice)).not.toThrow();
    expect(renderNotice(notice)).toContain('license_number: Field required');
  });

  it('proves the raw detail array is what crashed the page', () => {
    expect(() => renderNotice(FASTAPI_422.detail)).toThrow(/Objects are not valid/);
  });
});
