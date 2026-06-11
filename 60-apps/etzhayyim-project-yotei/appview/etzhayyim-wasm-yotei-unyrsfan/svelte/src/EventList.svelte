<script lang="ts">
  /** Upcoming events list with cancel action. */

  interface Props {
    xrpc: <T>(nsid: string, params?: Record<string, unknown>) => Promise<T>;
  }
  let { xrpc }: Props = $props();

  interface EventItem { id: string; title: string; startAt: string; endAt: string; location: string; status: string; }

  let calendarId = $state('');
  let events = $state<EventItem[]>([]);
  let loading = $state(false);

  /** Load upcoming events. */
  async function load(): Promise<void> {
    if (!calendarId) return;
    loading = true;
    const now = new Date().toISOString();
    const res = await xrpc<{ events: EventItem[] }>('com.etzhayyim.apps.yotei.listEvents', { calendarId, dateFrom: now });
    events = res.events ?? [];
    loading = false;
  }

  /** Cancel an event. */
  async function cancel(id: string): Promise<void> {
    await xrpc('com.etzhayyim.apps.yotei.cancelEvent', { id });
    await load();
  }

  /** Format datetime for display. */
  function fmtDt(iso: string): string {
    if (!iso) return '';
    const d = new Date(iso);
    return d.toLocaleDateString('ja-JP', { month: 'short', day: 'numeric', weekday: 'short' })
      + ' ' + d.toLocaleTimeString('ja-JP', { hour: '2-digit', minute: '2-digit' });
  }
</script>

<div class="px-4 pt-4">
  <h2 class="text-[17px] font-bold text-white mb-4">Upcoming Events</h2>

  <div class="flex items-center gap-2 mb-4">
    <input
      type="text"
      bind:value={calendarId}
      placeholder="Calendar ID"
      class="flex-1 px-3 py-2 rounded-lg bg-white/5 border border-white/10 text-white text-[15px]"
    />
    <button
      onclick={load}
      class="px-4 py-2 rounded-lg bg-indigo-500 text-white text-[15px] min-h-[44px] active:opacity-80"
    >
      Load
    </button>
  </div>

  {#if loading}
    <div class="text-center text-white/50 py-8">Loading...</div>
  {:else if events.length === 0}
    <div class="text-center text-white/50 py-8 text-[13px]">No upcoming events</div>
  {:else}
    <div class="flex flex-col gap-2">
      {#each events as evt}
        <div class="p-3 rounded-lg bg-white/5 border border-white/10">
          <div class="flex items-start justify-between">
            <div class="flex-1">
              <div class="text-[15px] text-white font-medium">{evt.title}</div>
              <div class="text-[13px] text-white/50 mt-0.5">
                {fmtDt(evt.startAt)} — {fmtDt(evt.endAt)}
              </div>
              {#if evt.location}
                <div class="text-[11px] text-white/50 mt-0.5">{evt.location}</div>
              {/if}
            </div>
            <button
              onclick={() => cancel(evt.id)}
              class="text-[11px] text-red-400 px-2 py-1 rounded active:opacity-80 min-h-[44px] flex items-center"
            >
              Cancel
            </button>
          </div>
        </div>
      {/each}
    </div>
  {/if}
</div>
