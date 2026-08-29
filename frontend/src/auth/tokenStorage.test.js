import { describe, expect, it, beforeEach, afterEach } from 'vitest';
import { tokenStorage, TOKEN_KEY } from './tokenStorage';

class LocalStorageShim {
  constructor() {
    this.store = new Map();
  }
  getItem(key) {
    return this.store.has(key) ? this.store.get(key) : null;
  }
  setItem(key, value) {
    this.store.set(key, String(value));
  }
  removeItem(key) {
    this.store.delete(key);
  }
}

let localStorage;

beforeEach(() => {
  localStorage = new LocalStorageShim();
  globalThis.window = { localStorage };
});

afterEach(() => {
  delete globalThis.window;
});

describe('tokenStorage', () => {
  it('reads an empty storage as null', () => {
    expect(tokenStorage.get()).toBeNull();
  });

  it('stores and reads a token under the fixed key', () => {
    tokenStorage.set('tok-123');
    expect(localStorage.getItem(TOKEN_KEY)).toBe('tok-123');
    expect(tokenStorage.get()).toBe('tok-123');
  });

  it('clears the token', () => {
    tokenStorage.set('tok-123');
    tokenStorage.clear();
    expect(localStorage.getItem(TOKEN_KEY)).toBeNull();
    expect(tokenStorage.get()).toBeNull();
  });

  it('removes only its own key', () => {
    localStorage.setItem('other-key', 'keep');
    tokenStorage.set('tok-123');
    tokenStorage.clear();
    expect(localStorage.getItem('other-key')).toBe('keep');
  });
});