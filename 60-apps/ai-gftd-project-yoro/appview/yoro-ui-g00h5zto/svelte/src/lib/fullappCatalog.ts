export type FullappHeroEntry = {
	id: string;
	name: string;
	title: string;
	description: string;
	url: string;
	accent: string;
};

export const fullappHeroCatalog: FullappHeroEntry[] = [
	{
		id: '6ir',
		name: '6IR',
		title: 'Industry 6 Cross-Sector Agent Directory',
		description: 'ISIC / States / ISCO / COFOG / CPC を横断する directory intelligence を yoro の先頭から直接プレビューする。',
		url: 'https://6ir.etzhayyim.com/?embed=hero&surface=yoro',
		accent: '#1185FE',
	},
];
