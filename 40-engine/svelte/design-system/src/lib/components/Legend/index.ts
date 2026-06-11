import type { ComponentProps } from 'svelte';
import LegendComponent from './Legend.svelte';

export const Legend = LegendComponent;
export type LegendSize = NonNullable<ComponentProps<typeof LegendComponent>['size']>;
