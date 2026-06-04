import type { PageServerLoad } from './$types';

export const load: PageServerLoad = async ({ params, platform }) => {
	return {
		og: {},
		jsonLd: undefined,
	};
};
