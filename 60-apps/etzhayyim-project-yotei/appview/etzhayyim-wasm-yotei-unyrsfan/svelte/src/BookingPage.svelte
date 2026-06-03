<script lang="ts">
  /** Public booking page — select duration and preferred time. */

  interface Props {
    xrpc: <T>(nsid: string, params?: Record<string, unknown>) => Promise<T>;
  }
  let { xrpc }: Props = $props();

  interface BookingItem { id: string; requesterDid: string; durationMin: number; status: string; confirmedSlot: string; createdAt: string; }

  let calendarId = $state('');
  let requesterDid = $state('');
  let durationMin = $state(30);
  let message = $state('');
  let bookings = $state<BookingItem[]>([]);
  let submitting = $state(false);
  let result = $state('');

  /** Submit a booking proposal. */
  async function propose(): Promise<void> {
    if (!calendarId || !requesterDid) return;
    submitting = true;
    result = '';
    const res = await xrpc<{ id: string; status: string }>('com.etzhayyim.apps.yotei.proposeBooking', {
      calendarId,
      requesterDid,
      durationMin,
      message,
    });
    result = `Booking ${res.id} — ${res.status}`;
    submitting = false;
    await loadBookings();
  }

  /** Load existing bookings. */
  async function loadBookings(): Promise<void> {
    if (!calendarId) return;
    const res = await xrpc<{ bookings: BookingItem[] }>('com.etzhayyim.apps.yotei.listBookings', { calendarId });
    bookings = res.bookings ?? [];
  }

  const STATUS_COLORS: Record<string, string> = {
    proposed: 'bg-yellow-500/20 text-yellow-300',
    confirmed: 'bg-green-500/20 text-green-300',
    declined: 'bg-red-500/20 text-red-300',
    cancelled: 'bg-white/10 text-white/40',
  };
</script>

<div class="px-4 pt-4">
  <h2 class="text-[17px] font-bold text-white mb-4">Book a Meeting</h2>

  <!-- Booking form -->
  <div class="flex flex-col gap-3 mb-6">
    <input
      type="text"
      bind:value={calendarId}
      placeholder="Calendar ID"
      class="px-3 py-2 rounded-lg bg-white/5 border border-white/10 text-white text-[15px]"
    />
    <input
      type="text"
      bind:value={requesterDid}
      placeholder="Your DID (did:web:...)"
      class="px-3 py-2 rounded-lg bg-white/5 border border-white/10 text-white text-[15px]"
    />
    <div class="flex gap-2 items-center">
      <span class="text-[13px] text-white/50">Duration</span>
      <select
        bind:value={durationMin}
        class="px-3 py-2 rounded-lg bg-white/5 border border-white/10 text-white text-[15px]"
      >
        <option value={15}>15 min</option>
        <option value={30}>30 min</option>
        <option value={45}>45 min</option>
        <option value={60}>60 min</option>
        <option value={90}>90 min</option>
      </select>
    </div>
    <textarea
      bind:value={message}
      placeholder="Message (optional)"
      rows="2"
      class="px-3 py-2 rounded-lg bg-white/5 border border-white/10 text-white text-[15px] resize-none"
    ></textarea>
    <button
      onclick={propose}
      disabled={submitting || !calendarId || !requesterDid}
      class="px-4 py-3 rounded-lg bg-indigo-500 text-white text-[15px] font-medium min-h-[44px] active:opacity-80 disabled:opacity-40"
    >
      {submitting ? 'Proposing...' : 'Propose Booking'}
    </button>
    {#if result}
      <div class="text-[13px] text-green-400 text-center">{result}</div>
    {/if}
  </div>

  <!-- Bookings list -->
  <div class="flex items-center justify-between mb-3">
    <h3 class="text-[15px] font-medium text-white">Bookings</h3>
    <button
      onclick={loadBookings}
      class="text-[13px] text-indigo-400 active:opacity-80"
    >
      Refresh
    </button>
  </div>

  {#if bookings.length === 0}
    <div class="text-center text-white/50 py-6 text-[13px]">No bookings yet</div>
  {:else}
    <div class="flex flex-col gap-2">
      {#each bookings as bk}
        <div class="p-3 rounded-lg bg-white/5 border border-white/10">
          <div class="flex items-center justify-between mb-1">
            <span class="text-[13px] text-white/50 font-mono">{bk.id}</span>
            <span class={`text-[11px] px-2 py-0.5 rounded-full ${STATUS_COLORS[bk.status] ?? ''}`}>{bk.status}</span>
          </div>
          <div class="text-[13px] text-white">{bk.requesterDid}</div>
          <div class="text-[11px] text-white/50">{bk.durationMin}min — {bk.createdAt?.slice(0, 16)}</div>
          {#if bk.confirmedSlot}
            <div class="text-[11px] text-green-400 mt-1">Confirmed: {bk.confirmedSlot}</div>
          {/if}
        </div>
      {/each}
    </div>
  {/if}
</div>
