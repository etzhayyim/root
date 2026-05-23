import type { ComponentProps } from 'svelte';
import SelectComponent from './Select.svelte';

export const Select = SelectComponent;
export type SelectBlockSize = NonNullable<ComponentProps<typeof SelectComponent>['blockSize']>;
