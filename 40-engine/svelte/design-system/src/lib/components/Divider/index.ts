import type { ComponentProps } from 'svelte';
import DividerComponent from './Divider.svelte';

export const Divider = DividerComponent;
export type DividerColor = NonNullable<ComponentProps<typeof DividerComponent>['color']>;
