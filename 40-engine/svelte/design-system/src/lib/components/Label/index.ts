import type { ComponentProps } from 'svelte';
import LabelComponent from './Label.svelte';

export const Label = LabelComponent;
export type LabelSize = NonNullable<ComponentProps<typeof LabelComponent>['size']>;
