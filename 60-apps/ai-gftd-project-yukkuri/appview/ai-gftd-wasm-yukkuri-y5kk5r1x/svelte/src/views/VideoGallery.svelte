<script lang="ts">
  import { onMount } from 'svelte';
  import { listVideos, STATUS_LABEL, STATUS_COLOR, rkeyFromUri, type VideoSummary } from '../lib/api.js';

  let { go }: { go: (path: string) => void } = $props();

  let videos: VideoSummary[] = $state([]);
  let loading = $state(true);
  let error = $state('');
  let statusFilter = $state('');
  let offset = $state(0);
  const LIMIT = 20;

  async function load() {
    loading = true;
    error = '';
    try {
      const res = await listVideos({ status: statusFilter || undefined, offset, limit: LIMIT });
      videos = res.videos;
    } catch (e) {
      error = String((e as Error).message);
    } finally {
      loading = false;
    }
  }

  onMount(load);

  function handleFilter(s: string) {
    statusFilter = s;
    offset = 0;
    load();
  }

  const STATUS_FILTERS = ['', 'published', 'rendered', 'script', 'queued', 'rejected'];
  const STATUS_FILTER_LABEL: Record<string, string> = {
    '': 'すべて',
    published: '公開済',
    rendered: 'レンダー済',
    script: '台本生成済',
    queued: 'キュー待ち',
    rejected: '却下',
  };
</script>

<div class="gallery">
  <div class="toolbar">
    <h2>🎬 動画一覧</h2>
    <div class="filters">
      {#each STATUS_FILTERS as s}
        <button
          class:active={statusFilter === s}
          onclick={() => handleFilter(s)}
        >{STATUS_FILTER_LABEL[s]}</button>
      {/each}
    </div>
    <button class="compose-btn" onclick={() => go('/compose')}>＋ 新規作成</button>
  </div>

  {#if loading}
    <div class="center">読み込み中…</div>
  {:else if error}
    <div class="center error">{error}</div>
  {:else if videos.length === 0}
    <div class="center muted">動画がありません。「新規作成」からゆっくり動画を生成できます。</div>
  {:else}
    <div class="grid">
      {#each videos as v}
        {@const rkey = rkeyFromUri(v.videoUri)}
        <button class="card" onclick={() => go(`/video/${rkey}`)}>
          <div class="card-head">
            <span class="badge" style="background:{STATUS_COLOR[v.status] ?? '#555'}">
              {STATUS_LABEL[v.status] ?? v.status}
            </span>
            <span class="date">{v.createdAt ? v.createdAt.slice(0, 10) : ''}</span>
          </div>
          <div class="title">{v.title || '(タイトルなし)'}</div>
          {#if v.topic}
            <div class="topic">{v.topic.slice(0, 80)}{v.topic.length > 80 ? '…' : ''}</div>
          {/if}
          <div class="meta">
            {#if v.sceneCount}<span>シーン {v.sceneCount}</span>{/if}
            {#if v.lineCount}<span>セリフ {v.lineCount}</span>{/if}
          </div>
        </button>
      {/each}
    </div>
  {/if}
</div>

<style>
  .gallery { padding: 24px; height: 100%; box-sizing: border-box; overflow-y: auto; }
  .toolbar {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 20px;
    flex-wrap: wrap;
  }
  h2 { margin: 0; font-size: 1.1rem; font-weight: 600; }
  .filters { display: flex; gap: 6px; flex-wrap: wrap; }
  .filters button {
    background: #1a1d26;
    border: 1px solid #2a2d3a;
    color: #a0a4b0;
    border-radius: 14px;
    padding: 4px 12px;
    font-size: 0.78rem;
    cursor: pointer;
  }
  .filters button:hover { color: #fff; background: #22253a; }
  .filters button.active { color: #fff; background: #2a3a5c; border-color: #5ab0ff; }
  .compose-btn {
    margin-left: auto;
    background: #2a3a5c;
    border: 1px solid #5ab0ff;
    color: #90caf9;
    border-radius: 6px;
    padding: 6px 16px;
    font-size: 0.85rem;
    cursor: pointer;
    white-space: nowrap;
  }
  .compose-btn:hover { background: #344566; }
  .center { display: flex; align-items: center; justify-content: center; height: 200px; color: #666; font-size: 0.9rem; }
  .error { color: #f44336; }
  .muted { color: #555; }
  .grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
    gap: 14px;
  }
  .card {
    background: #14161f;
    border: 1px solid #22252d;
    border-radius: 10px;
    padding: 14px;
    text-align: left;
    cursor: pointer;
    transition: border-color 0.15s, background 0.15s;
    display: flex;
    flex-direction: column;
    gap: 8px;
  }
  .card:hover { border-color: #3a4466; background: #171a26; }
  .card-head { display: flex; align-items: center; justify-content: space-between; }
  .badge {
    display: inline-block;
    padding: 2px 8px;
    border-radius: 10px;
    font-size: 0.7rem;
    font-weight: 600;
    color: #fff;
  }
  .date { font-size: 0.72rem; color: #555; }
  .title { font-size: 0.9rem; font-weight: 600; color: #e0e4f0; line-height: 1.4; }
  .topic { font-size: 0.78rem; color: #7a8090; line-height: 1.5; }
  .meta { display: flex; gap: 8px; font-size: 0.72rem; color: #555; margin-top: 2px; }
</style>
