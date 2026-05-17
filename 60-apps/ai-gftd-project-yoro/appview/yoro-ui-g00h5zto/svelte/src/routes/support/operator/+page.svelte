<script lang="ts">
  import { operatingEntity, operatorDisclaimer } from '$lib/legal';
</script>

<svelte:head>
  <title>Operating Entity — amanomibashira | YORO</title>
  <meta
    name="description"
    content="YORO and connected services are operated by amanomibashira (עץ חיים), a religious voluntary association (宗教法人・任意団体) registered on a public blockchain."
  />
  <link rel="canonical" href="https://yoro.etzhayyim.com/support/operator" />
  {@html `<script type="application/ld+json">${JSON.stringify({
    '@context': 'https://schema.org',
    '@type': 'Organization',
    name: operatingEntity.name,
    alternateName: [operatingEntity.nameHebrew, operatingEntity.nameJa, operatingEntity.form],
    url: 'https://yoro.etzhayyim.com/support/operator',
    email: operatingEntity.contact,
    description: `${operatingEntity.formEn}. Constitution and member roster: ${operatingEntity.registry}. ${operatingEntity.registryNote}`
  })}</script>`}
</svelte:head>

<div class="mx-auto flex w-full max-w-[860px] flex-col gap-6 px-4 py-6 sm:px-6 lg:px-8">
  <section
    class="rounded-[28px] border border-[var(--gv2-border,#333333)] bg-[linear-gradient(180deg,color-mix(in_srgb,var(--gv2-bg-card,#222222)_86%,white_6%),var(--gv2-bg-primary,#1a1a1a))] p-6 shadow-[0_24px_80px_rgba(0,0,0,0.24)]"
  >
    <div class="flex flex-wrap items-center gap-2 text-[11px] font-semibold uppercase tracking-[0.18em] text-[var(--gv2-text-muted,#666666)]">
      <span>Compliance</span>
      <span aria-hidden="true">•</span>
      <span>Operating Entity</span>
    </div>
    <h1 class="mt-3 text-3xl font-semibold tracking-[-0.03em] text-[var(--gv2-text-primary,#ffffff)]">
      {operatingEntity.name} <span class="opacity-60">— {operatingEntity.nameHebrew}</span>
    </h1>
    <p class="mt-3 max-w-[62ch] text-sm leading-7 text-[var(--gv2-text-secondary,#a0a0a0)]">
      YORO and connected services are operated by <strong>{operatingEntity.name}</strong>
      ({operatingEntity.nameJa} / {operatingEntity.nameHebrew}), a {operatingEntity.formEn}
      ({operatingEntity.form}).
    </p>
  </section>

  <section class="rounded-[24px] border border-[var(--gv2-border,#333333)] bg-[color-mix(in_srgb,var(--gv2-bg-card,#222222)_82%,transparent)] p-5">
    <h2 class="text-lg font-semibold tracking-[-0.02em] text-[var(--gv2-text-primary,#ffffff)]">Identity</h2>
    <dl class="mt-3 grid gap-3 text-sm leading-7 text-[var(--gv2-text-secondary,#a0a0a0)] sm:grid-cols-[160px_1fr]">
      <dt class="font-semibold text-[var(--gv2-text-primary,#ffffff)]">Name</dt>
      <dd>{operatingEntity.name} ({operatingEntity.nameHebrew}, {operatingEntity.nameJa})</dd>
      <dt class="font-semibold text-[var(--gv2-text-primary,#ffffff)]">Form</dt>
      <dd>{operatingEntity.form} — {operatingEntity.formEn}</dd>
      <dt class="font-semibold text-[var(--gv2-text-primary,#ffffff)]">Registry</dt>
      <dd>{operatingEntity.registry}</dd>
      <dt class="font-semibold text-[var(--gv2-text-primary,#ffffff)]">Contact</dt>
      <dd><a class="underline decoration-dotted" href={`mailto:${operatingEntity.contact}`}>{operatingEntity.contact}</a></dd>
    </dl>
  </section>

  <section class="rounded-[24px] border border-amber-500/30 bg-amber-500/5 p-5">
    <h2 class="text-lg font-semibold tracking-[-0.02em] text-amber-200">Important Notice — 重要事項</h2>
    <p class="mt-3 text-sm leading-7 text-[var(--gv2-text-secondary,#a0a0a0)]">{operatingEntity.registryNote}</p>
  </section>

  <section class="rounded-[24px] border border-[var(--gv2-border,#333333)] bg-[color-mix(in_srgb,var(--gv2-bg-card,#222222)_82%,transparent)] p-5">
    <h2 class="text-lg font-semibold tracking-[-0.02em] text-[var(--gv2-text-primary,#ffffff)]">Disclaimer</h2>
    <div class="mt-3 grid gap-3 text-sm leading-7 text-[var(--gv2-text-secondary,#a0a0a0)]">
      {#each operatorDisclaimer as paragraph}
        <p>{paragraph}</p>
      {/each}
    </div>
  </section>

  <section class="rounded-[24px] border border-[var(--gv2-border,#333333)] bg-[color-mix(in_srgb,var(--gv2-bg-card,#222222)_82%,transparent)] p-5">
    <h2 class="text-lg font-semibold tracking-[-0.02em] text-[var(--gv2-text-primary,#ffffff)]">See also</h2>
    <ul class="mt-3 grid gap-2 text-sm leading-7 text-[var(--gv2-text-secondary,#a0a0a0)]">
      <li><a class="underline decoration-dotted" href="/terms">Terms of Use</a> — operated by amanomibashira</li>
      <li><a class="underline decoration-dotted" href="/privacy">Privacy Policy</a> — controller: amanomibashira</li>
      <li><a class="underline decoration-dotted" href="/support">Support</a></li>
    </ul>
  </section>
</div>
