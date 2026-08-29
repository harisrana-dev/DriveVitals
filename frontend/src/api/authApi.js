import { apiClient } from './apiClient';
import { endpoints } from './endpoints';

const authApi = {
  async signup({ email, password, fullName }) {
    return apiClient.post(endpoints.auth.signup, {
      email,
      password,
      full_name: fullName,
    });
  },
  async login({ email, password }) {
    return apiClient.post(endpoints.auth.login, { email, password });
  },
  async logout(token) {
    return apiClient.post(
      endpoints.auth.logout,
      undefined,
      { headers: token ? { Authorization: `Bearer ${token}` } : undefined },
    );
  },
  async me(token) {
    return apiClient.get(
      endpoints.auth.me,
      { headers: token ? { Authorization: `Bearer ${token}` } : undefined },
    );
  },
};

export { authApi };