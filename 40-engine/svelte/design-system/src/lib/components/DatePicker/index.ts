import type { ComponentProps } from 'svelte';
import DatePickerComponent from './DatePicker.svelte';

export const DatePicker = DatePickerComponent;
export type DatePickerSize = NonNullable<ComponentProps<typeof DatePickerComponent>['size']>;
export { default as DatePickerYear } from './parts/DatePickerYear.svelte';
export { default as DatePickerMonth } from './parts/DatePickerMonth.svelte';
export { default as DatePickerDate } from './parts/DatePickerDate.svelte';
export { default as DatePickerCalendarButton } from './parts/DatePickerCalendarButton.svelte';
