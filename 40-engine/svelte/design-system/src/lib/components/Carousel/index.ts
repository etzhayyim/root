import type { ComponentProps } from 'svelte';
import CarouselComponent from './Carousel.svelte';

export const Carousel = CarouselComponent;
export type CarouselSlide = ComponentProps<typeof CarouselComponent>['slides'][number];
