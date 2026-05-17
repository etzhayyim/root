export interface CardListItem {
  id: string;
  label: string;
  sublabel?: string;
  icon?: string;
  imageUrl?: string;
  action?: string;
}

export interface CardListPayload {
  title?: string;
  items: CardListItem[];
}

export interface CardFormFieldOption {
  label: string;
  value: string;
}

export interface CardFormField {
  name: string;
  label: string;
  type?: string;
  required?: boolean;
  placeholder?: string;
  value?: string;
  options?: CardFormFieldOption[];
}

export interface CardFormPayload {
  title?: string;
  action: string;
  submitLabel?: string;
  fields: CardFormField[];
}

export interface CardTableColumn {
  key: string;
  label: string;
  sortable?: boolean;
}

export interface CardTablePayload {
  title?: string;
  columns: CardTableColumn[];
  rows: Record<string, string | number | null | undefined>[];
}

export interface CardCarouselItem {
  title?: string;
  subtitle?: string;
  imageUrl?: string;
  action?: string;
}

export interface CardCarouselPayload {
  items: CardCarouselItem[];
}

export type CardChartType = 'bar' | 'line' | 'pie';

export interface CardChartSeries {
  name?: string;
  data: number[];
}

export interface CardChartPayload {
  title?: string;
  chartType: CardChartType;
  series: CardChartSeries[];
  labels?: string[];
}

export interface CardPollOption {
  id: string;
  label: string;
  count?: number;
}

export interface CardPollPayload {
  question: string;
  options: CardPollOption[];
  closed?: boolean;
}

export interface CardReceiptLineItem {
  desc: string;
  amount: number;
  qty?: number;
}

export interface CardReceiptPayload {
  title?: string;
  lineItems: CardReceiptLineItem[];
  total: number;
  currency: string;
  paid?: boolean;
}

export interface CardCodePayload {
  code: string;
  filename?: string;
  language?: string;
}

export interface CardCalendarEvent {
  id: string;
  title: string;
  start: string;
  end?: string;
  location?: string;
  color?: string;
}

export interface CardCalendarPayload {
  events: CardCalendarEvent[];
}

export interface CardKanbanCard {
  id: string;
  title: string;
  assignee?: string;
  color?: string;
}

export interface CardKanbanColumn {
  id: string;
  title: string;
  cards: CardKanbanCard[];
}

export interface CardKanbanPayload {
  columns: CardKanbanColumn[];
}

export interface CardConfirmationPayload {
  title: string;
  message: string;
  action: string;
  confirmLabel: string;
  cancelLabel?: string;
  destructive?: boolean;
}

export type CardMetricTrend = 'up' | 'down' | 'flat';

export interface CardMetricItem {
  label: string;
  value: string | number;
  unit?: string;
  trend?: CardMetricTrend;
  sparkline?: number[];
}

export interface CardMetricDashboardPayload {
  metrics: CardMetricItem[];
}

export interface CardImageGalleryImage {
  url: string;
  alt?: string;
  caption?: string;
}

export interface CardImageGalleryPayload {
  images: CardImageGalleryImage[];
}

export interface CardEmbedPayload {
  url: string;
  title?: string;
  width?: string | number;
  height?: string | number;
}

export type CardServiceStatus = 'online' | 'degraded' | 'offline' | 'maintenance';

export interface CardServicePayload {
  name: string;
  status: CardServiceStatus;
  icon?: string;
  version?: string;
  description?: string;
  capabilities?: string[];
}

export type CardSystemHealth = 'healthy' | 'warning' | 'critical';

export interface CardSystemPayload {
  name: string;
  healthStatus: CardSystemHealth;
  icon?: string;
  version?: string;
  description?: string;
  components?: string[];
  uptime?: string;
}

export interface CardPersonPayload {
  name: string;
  avatar?: string;
  occupation?: string;
  description?: string;
  tags?: string[];
  competenceBadge?: string;
}

export interface CardOrganizationPayload {
  name: string;
  logo?: string;
  jurisdiction?: string;
  description?: string;
  tags?: string[];
  memberCount?: number;
}

export interface CardGameCharacter {
  id: string;
  name: string;
  role?: string;
  skin_hue: number;
}

export interface CardGameAction {
  name: string;
  label: string;
  primary?: boolean;
}

export interface CardGamePayload {
  title: string;
  description?: string;
  genre: string;
  thumbnail_url?: string;
  play_url: string;
  max_players: number;
  characters?: CardGameCharacter[];
  actions?: CardGameAction[];
}
