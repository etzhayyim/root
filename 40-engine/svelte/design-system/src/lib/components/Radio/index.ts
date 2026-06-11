import type { ComponentProps } from 'svelte';
import RadioComponent from './Radio.svelte';

export const Radio = RadioComponent;
export type RadioSize = NonNullable<ComponentProps<typeof RadioComponent>['size']>;
