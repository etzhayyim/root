import { pageStore, navigatingStore, updatedStore } from "./router";

export const page = {
  subscribe: pageStore.subscribe,
};

export const navigating = {
  subscribe: navigatingStore.subscribe,
};

export const updated = {
  subscribe: updatedStore.subscribe,
  check: async () => false,
};

