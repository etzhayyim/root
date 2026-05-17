export interface GfAppLink {
	id: string;
	name: string;
	shortName?: string;
	href: string;
	icon: string;
	category: 'Orgs' | 'Services' | 'Systems';
	description?: string;
	external?: boolean;
}
