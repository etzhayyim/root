import type { ComponentProps } from 'svelte';
import CheckboxComponent from './Checkbox.svelte';

export const Checkbox = CheckboxComponent;
export type CheckboxSize = NonNullable<ComponentProps<typeof CheckboxComponent>['size']>;
