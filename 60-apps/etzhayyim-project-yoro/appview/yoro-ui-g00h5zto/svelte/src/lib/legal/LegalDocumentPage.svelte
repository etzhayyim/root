<script lang="ts">
  import type { LegalDocument } from './content.js';

  interface Props {
    document: LegalDocument;
  }

  const { document }: Props = $props();

  const canonicalPath = $derived('/' + document.did.split(':').pop());
</script>

<svelte:head>
  <title>{document.title} | YORO</title>
  <meta name="description" content={document.summary} />
  <meta name="at:did" content={document.did} />
  <link rel="canonical" href="https://yoro.etzhayyim.com{canonicalPath}" />
  {@html `<script type="application/ld+json">${JSON.stringify({
    "@context": "https://schema.org",
    "@type": "WebPage",
    "@id": document.did,
    "name": document.title,
    "description": document.summary,
    "url": `https://yoro.etzhayyim.com${canonicalPath}`,
    "dateModified": document.lastUpdated,
    "publisher": {
      "@type": "Organization",
      "name": "amanomibashira",
      "alternateName": ["עץ חיים", "宗教法人 amanomibashira (任意団体)"],
      "url": "https://yoro.etzhayyim.com/support/operator",
      "description": "Religious voluntary association (宗教法人・任意団体), constitution and member roster registered on a public blockchain. Not an incorporated 宗教法人 under the Japanese 宗教法人法."
    }
  })}</script>`}
</svelte:head>

<div class="mx-auto flex w-full max-w-[860px] flex-col gap-6 px-4 py-6 sm:px-6 lg:px-8">
  <section class="rounded-[28px] border border-[var(--gv2-border,#333333)] bg-[linear-gradient(180deg,color-mix(in_srgb,var(--gv2-bg-card,#222222)_86%,white_6%),var(--gv2-bg-primary,#1a1a1a))] p-6 shadow-[0_24px_80px_rgba(0,0,0,0.24)]">
    <div class="flex flex-wrap items-center gap-2 text-[11px] font-semibold uppercase tracking-[0.18em] text-[var(--gv2-text-muted,#666666)]">
      <span>Compliance</span>
      <span aria-hidden="true">•</span>
      <span>YORO</span>
    </div>
    <h1 class="mt-3 text-3xl font-semibold tracking-[-0.03em] text-[var(--gv2-text-primary,#ffffff)]">{document.title}</h1>
    <p class="mt-3 max-w-[62ch] text-sm leading-7 text-[var(--gv2-text-secondary,#a0a0a0)]">{document.summary}</p>
    <div class="mt-5 flex flex-wrap gap-3 text-xs text-[var(--gv2-text-muted,#666666)]">
      <span class="rounded-full border border-[var(--gv2-border,#333333)] px-3 py-1">Effective {document.effectiveDate}</span>
      <span class="rounded-full border border-[var(--gv2-border,#333333)] px-3 py-1">Last updated {document.lastUpdated}</span>
    </div>
  </section>

  <div class="grid gap-4">
    {#each document.sections as section}
      <section class="rounded-[24px] border border-[var(--gv2-border,#333333)] bg-[color-mix(in_srgb,var(--gv2-bg-card,#222222)_82%,transparent)] p-5">
        <h2 class="text-lg font-semibold tracking-[-0.02em] text-[var(--gv2-text-primary,#ffffff)]">{section.heading}</h2>
        <div class="mt-3 grid gap-3 text-sm leading-7 text-[var(--gv2-text-secondary,#a0a0a0)]">
          {#each section.body as paragraph}
            <p>{paragraph}</p>
          {/each}
        </div>
      </section>
    {/each}
  </div>
</div>
