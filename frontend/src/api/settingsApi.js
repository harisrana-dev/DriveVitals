import { apiClient } from './apiClient';
import { endpoints } from './endpoints';

const settingsApi = {
  /** Fetch the full settings payload (account + system + analytics). */
  async getSettings() {
    return apiClient.get(endpoints.settings.all);
  },

  /** Fetch a single settings category. */
  async getCategory(category) {
    return apiClient.get(endpoints.settings.category(category));
  },

  /** Update a settings category (admin-only). */
  async updateCategory(category, data) {
    return apiClient.patch(endpoints.settings.category(category), data);
  },
};

export { settingsApi };
