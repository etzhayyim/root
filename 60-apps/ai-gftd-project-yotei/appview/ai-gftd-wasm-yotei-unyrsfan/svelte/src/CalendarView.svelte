<script lang="ts">
  /** Weekly calendar view with availability slots and events. */

  interface Props {
    xrpc: <T>(nsid: string, params?: Record<string, unknown>) => Promise<T>;
  }
  let { xrpc }: Props = $props();

  interface AvailSlot { id: string; dayOfWeek: number; startTime: string; endTime: string; recurring: boolean; }
  interface EventItem { id: string; title: string; startAt: string; endAt: string; status: string; }

  let availability = $state<AvailSlot[]>([]);
  let events = $state<EventItem[]>([]);
  let calendarId = $state('');
  let loading = $state(false);
  let weekOffset = $state(0);

  const DAY_NAMES = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
  const HOURS = Array.from({ length: 14 }, (_, i) => i + 7); // 07:00-20:00

  /** Get Monday of the current display week. */
  function getWeekStart(): Date {
    const d = new Date();
    d.setDate(d.getDate() - d.getDay() + 1 + weekOffset * 7);
    d.setHours(0, 0, 0, 0);
    return d;
  }

  /** Format date as YYYY-MM-DD. */
  function fmtDate(d: Date): string {
    return d.toISOString().slice(0, 10);
  }

  /** Load availability and events for current calendar. */
  async function loadWeek(): Promise<void> {
    if (!calendarId) return;
    loading = true;
    const start = getWeekStart();
    const end = new Date(start);
    end.setDate(end.getDate() + 6);

    const [availRes, eventRes] = await Promise.all([
      xrpc<{ availability: AvailSlot[] }>('com.etzhayyim.apps.yotei.getAvailability', { calendarId }),
      xrpc<{ events: EventItem[] }>('com.etzhayyim.apps.yotei.listEvents', { calendarId, dateFrom: fmtDate(start), dateTo: fmtDate(end) }),
    ]);
    availability = availRes.availability ?? [];
    events = eventRes.events ?? [];
    loading = false;
  }

  /** Check if an hour slot is available for a given day-of-week. */
  function isAvailable(dow: number, hour: number): boolean {
    const hhmm = `${hour.toString().padStart(2, '0')}:00`;
    return availability.some(a =>
      a.dayOfWeek === dow && a.startTime <= hhmm && a.endTime > hhmm,
    );
  }

  /** Get events overlapping a given hour on a specific date. */
  function eventsAt(dateStr: string, hour: number): EventItem[] {
    return events.filter(e => {
      const eDate = e.startAt.slice(0, 10);
      const eHour = parseInt(e.startAt.slice(11, 13), 10);
      return eDate === dateStr && eHour === hour;
    });
  }
</script>

<div class="px-4 pt-4">
  <!-- Calendar selector -->
  <div class="flex items-center gap-2 mb-4">
    <input
      type="text"
      bind:value={calendarId}
      placeholder="Calendar ID"
      class="flex-1 px-3 py-2 rounded-lg bg-white/5 border border-white/10 text-white text-[15px]"
    />
    <button
      onclick={loadWeek}
      class="px-4 py-2 rounded-lg bg-indigo-500 text-white text-[15px] min-h-[44px] active:opacity-80"
    >
      Load
    </button>
  </div>

  <!-- Week navigation -->
  <div class="flex items-center justify-between mb-4">
    <button
      onclick={() => { weekOffset--; loadWeek(); }}
      class="px-3 py-2 rounded-lg bg-white/5 border border-white/10 text-white min-h-[44px] active:opacity-80"
    >
      Prev
    </button>
    <span class="text-[15px] text-white font-medium">
      {fmtDate(getWeekStart())} week
    </span>
    <button
      onclick={() => { weekOffset++; loadWeek(); }}
      class="px-3 py-2 rounded-lg bg-white/5 border border-white/10 text-white min-h-[44px] active:opacity-80"
    >
      Next
    </button>
  </div>

  {#if loading}
    <div class="text-center text-white/50 py-8">Loading...</div>
  {:else}
    <!-- Weekly grid (mobile: horizontal scroll) -->
    <div class="overflow-x-auto -mx-4 px-4">
      <table class="w-full min-w-[560px] border-collapse text-[13px]">
        <thead>
          <tr>
            <th class="w-12 text-white/50 font-normal"></th>
            {#each Array.from({ length: 7 }, (_, i) => i) as dow}
              {@const d = new Date(getWeekStart())}
              {@const _ = d.setDate(d.getDate() + dow)}
              <th class="text-center text-white font-medium py-2">
                <div>{DAY_NAMES[(dow + 1) % 7]}</div>
                <div class="text-white/50 font-normal">{d.getDate()}</div>
              </th>
            {/each}
          </tr>
        </thead>
        <tbody>
          {#each HOURS as hour}
            <tr>
              <td class="text-white/50 text-right pr-2 align-top py-1">{hour}:00</td>
              {#each Array.from({ length: 7 }, (_, i) => i) as dow}
                {@const realDow = (dow + 1) % 7}
                {@const d = new Date(getWeekStart())}
                {@const __ = d.setDate(d.getDate() + dow)}
                {@const dateStr = fmtDate(d)}
                {@const avail = isAvailable(realDow, hour)}
                {@const hourEvents = eventsAt(dateStr, hour)}
                <td
                  class={`border border-white/10 h-10 align-top p-0.5 ${avail ? 'bg-indigo-500/10' : ''}`}
                >
                  {#each hourEvents as evt}
                    <div class="text-[11px] bg-indigo-500 text-white rounded px-1 py-0.5 truncate">
                      {evt.title}
                    </div>
                  {/each}
                </td>
              {/each}
            </tr>
          {/each}
        </tbody>
      </table>
    </div>
  {/if}
</div>
