import type { ComponentProps } from 'svelte';
import SeparatedDatePickerComponent from './SeparatedDatePicker.svelte';

export const SeparatedDatePicker = SeparatedDatePickerComponent;
export type SeparatedDatePickerSize = NonNullable<ComponentProps<typeof SeparatedDatePickerComponent>['size']>;
export { default as SeparatedDatePickerYear } from './parts/SeparatedDatePickerYear.svelte';
export { default as SeparatedDatePickerMonth } from './parts/SeparatedDatePickerMonth.svelte';
export { default as SeparatedDatePickerDate } from './parts/SeparatedDatePickerDate.svelte';
export { default as SeparatedDatePickerCalendarButton } from './parts/SeparatedDatePickerCalendarButton.svelte';
