<script lang="ts">
  import CalendarView from './CalendarView.svelte';
  import BookingPage from './BookingPage.svelte';
  import EventList from './EventList.svelte';

  /** Current route state. */
  let currentRoute = $state<'calendar' | 'booking' | 'events'>('calendar');

  /** XRPC helper — calls backend commands via /xrpc/{nsid}. */
  async function xrpc<T>(nsid: string, params: Record<string, unknown> = {}): Promise<T> {
    const res = await fetch(`/xrpc/${nsid}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(params),
    });
    return res.json() as Promise<T>;
  }

  const tabs = [
    { id: 'calendar' as const, label: 'Calendar', icon: '📅' },
    { id: 'booking' as const, label: 'Book', icon: '📋' },
    { id: 'events' as const, label: 'Events', icon: '📆' },
  ];
</script>

<div class="flex flex-col h-screen overflow-hidden bg-[#0a0a0a] text-white">
  <!-- Header -->
  <header class="flex items-center justify-center h-12 border-b border-white/10 shrink-0">
    <span class="text-[15px] font-bold tracking-wide">Yotei</span>
  </header>

  <!-- Content -->
  <main class="flex-1 overflow-y-auto">
    <div class="max-w-[600px] mx-auto pb-20">
      {#if currentRoute === 'calendar'}
        <CalendarView {xrpc} />
      {:else if currentRoute === 'booking'}
        <BookingPage {xrpc} />
      {:else if currentRoute === 'events'}
        <EventList {xrpc} />
      {/if}
    </div>
  </main>

  <!-- Bottom Tab Bar -->
  <nav class="flex items-center justify-around h-14 border-t border-white/10 bg-[#0a0a0a] shrink-0 safe-area-bottom">
    {#each tabs as tab}
      <button
        onclick={() => { currentRoute = tab.id; }}
        class="flex flex-col items-center gap-0.5 min-h-[44px] min-w-[44px] justify-center active:opacity-80
          {currentRoute === tab.id ? 'text-[#6366f1]' : 'text-white/50'}"
      >
        <span class="text-[18px]">{tab.icon}</span>
        <span class="text-[11px]">{tab.label}</span>
      </button>
    {/each}
  </nav>
</div>
