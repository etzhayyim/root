<script lang="ts">
  /**
   * Actor Designer — yoro.etzhayyim.com visual BPMN/DMN/Forms pipeline editor.
   *
   * Enables drag-drop actor pipeline design:
   * - BPMN tab: bpmn-js modeler for process flow design
   * - DMN tab: dmn-js decision table editor
   * - Forms tab: @bpmn-io/form-js form designer
   * - Preview tab: compiled ActorManifest JSON preview
   *
   * Flow: Design (BPMN) → Compile (compileBpmn XRPC) → Deploy (deployProcess XRPC)
   */
  import { onMount } from 'svelte';
  import { atProcedure } from '$lib/atproto-agent';

  // ── State ──

  let activeTab = $state<'bpmn' | 'dmn' | 'forms' | 'preview'>('bpmn');
  let bpmnContainer = $state<HTMLDivElement | null>(null);
  let dmnContainer = $state<HTMLDivElement | null>(null);
  let formsContainer = $state<HTMLDivElement | null>(null);

  let bpmnModeler: any = $state(null);
  let dmnModeler: any = $state(null);
  let formsEditor: any = $state(null);

  let actorDid = $state('');
  let actorName = $state('');
  let actorNanoid = $state('');

  let compiledManifest = $state<Record<string, unknown> | null>(null);
  let compileErrors = $state<string[]>([]);
  let compileWarnings = $state<string[]>([]);
  let deployStatus = $state<'idle' | 'compiling' | 'deploying' | 'success' | 'error'>('idle');
  let deployMessage = $state('');

  // ── BPMN Default Template ──

  const DEFAULT_BPMN = `<?xml version="1.0" encoding="UTF-8"?>
<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"
                  xmlns:bpmndi="http://www.omg.org/spec/BPMN/20100524/DI"
                  xmlns:dc="http://www.omg.org/spec/DD/20100524/DC"
                  xmlns:di="http://www.omg.org/spec/DD/20100524/DI"
                  id="Definitions_1" targetNamespace="https://etzhayyim.com/bpmn">
  <bpmn:process id="Process_1" name="New Actor Pipeline" isExecutable="true">
    <bpmn:startEvent id="StartEvent_1" name="Trigger">
      <bpmn:outgoing>Flow_1</bpmn:outgoing>
    </bpmn:startEvent>
    <bpmn:serviceTask id="Task_1" name="Graph Query" camunda:type="graph-query">
      <bpmn:incoming>Flow_1</bpmn:incoming>
      <bpmn:outgoing>Flow_2</bpmn:outgoing>
    </bpmn:serviceTask>
    <bpmn:endEvent id="EndEvent_1" name="Done">
      <bpmn:incoming>Flow_2</bpmn:incoming>
    </bpmn:endEvent>
    <bpmn:sequenceFlow id="Flow_1" sourceRef="StartEvent_1" targetRef="Task_1" />
    <bpmn:sequenceFlow id="Flow_2" sourceRef="Task_1" targetRef="EndEvent_1" />
  </bpmn:process>
  <bpmndi:BPMNDiagram id="BPMNDiagram_1">
    <bpmndi:BPMNPlane id="BPMNPlane_1" bpmnElement="Process_1">
      <bpmndi:BPMNShape id="_BPMNShape_StartEvent_1" bpmnElement="StartEvent_1">
        <dc:Bounds x="179" y="79" width="36" height="36" />
      </bpmndi:BPMNShape>
      <bpmndi:BPMNShape id="Task_1_di" bpmnElement="Task_1">
        <dc:Bounds x="270" y="57" width="100" height="80" />
      </bpmndi:BPMNShape>
      <bpmndi:BPMNShape id="EndEvent_1_di" bpmnElement="EndEvent_1">
        <dc:Bounds x="432" y="79" width="36" height="36" />
      </bpmndi:BPMNShape>
      <bpmndi:BPMNEdge id="Flow_1_di" bpmnElement="Flow_1">
        <di:waypoint x="215" y="97" />
        <di:waypoint x="270" y="97" />
      </bpmndi:BPMNEdge>
      <bpmndi:BPMNEdge id="Flow_2_di" bpmnElement="Flow_2">
        <di:waypoint x="370" y="97" />
        <di:waypoint x="432" y="97" />
      </bpmndi:BPMNEdge>
    </bpmndi:BPMNPlane>
  </bpmndi:BPMNDiagram>
</bpmn:definitions>`;

  // ── Lifecycle ──

  onMount(async () => {
    await initBpmnModeler();
  });

  /** Initialize bpmn-js modeler with dynamic import (tree-shaking). */
  async function initBpmnModeler() {
    if (!bpmnContainer) return;
    try {
      const { default: BpmnModeler } = await import('bpmn-js/lib/Modeler');
      bpmnModeler = new BpmnModeler({ container: bpmnContainer });
      await bpmnModeler.importXML(DEFAULT_BPMN);
      bpmnModeler.get('canvas').zoom('fit-viewport');
    } catch (e) {
      console.warn('[actor-designer] bpmn-js init failed:', e);
    }
  }

  /** Initialize dmn-js editor on tab switch. */
  async function initDmnModeler() {
    if (!dmnContainer || dmnModeler) return;
    try {
      const { default: DmnModeler } = await import('dmn-js/lib/Modeler');
      dmnModeler = new DmnModeler({ container: dmnContainer });
    } catch (e) {
      console.warn('[actor-designer] dmn-js init failed:', e);
    }
  }

  /** Initialize @bpmn-io/form-js editor on tab switch. */
  async function initFormsEditor() {
    if (!formsContainer || formsEditor) return;
    try {
      const { FormEditor } = await import('@bpmn-io/form-js-editor');
      formsEditor = new FormEditor({ container: formsContainer });
    } catch (e) {
      console.warn('[actor-designer] form-js init failed:', e);
    }
  }

  // ── Tab Switch ──

  function switchTab(tab: typeof activeTab) {
    activeTab = tab;
    if (tab === 'dmn') setTimeout(initDmnModeler, 0);
    if (tab === 'forms') setTimeout(initFormsEditor, 0);
    if (tab === 'preview') handleCompile();
  }

  // ── Compile ──

  /** Compile BPMN XML → ActorManifest via PDS XRPC. */
  async function handleCompile() {
    if (!bpmnModeler) return;
    deployStatus = 'compiling';
    compileErrors = [];
    compileWarnings = [];

    try {
      const { xml } = await bpmnModeler.saveXML({ format: true });

      // Get DMN XML if available
      let dmnXml: string | undefined;
      if (dmnModeler) {
        try {
          const dmnResult = await dmnModeler.saveXML({ format: true });
          dmnXml = dmnResult.xml;
        } catch { /* no DMN */ }
      }

      // Get form schemas if available
      let formSchemas: Record<string, unknown> | undefined;
      if (formsEditor) {
        try {
          const schema = formsEditor.getSchema();
          if (schema) formSchemas = { default: schema };
        } catch { /* no forms */ }
      }

      const result = await atProcedure('com.etzhayyim.actor.compileBpmn', {
        bpmnXml: xml,
        did: actorDid || 'did:web:new-actor.etzhayyim.com',
        name: actorName || 'new-actor',
        nanoid: actorNanoid || 'new00000',
        dmnXml,
        formSchemas,
      }) as { success: boolean; manifest?: Record<string, unknown>; errors: string[]; warnings: string[] };

      compiledManifest = result.manifest || null;
      compileErrors = result.errors || [];
      compileWarnings = result.warnings || [];
      deployStatus = result.success ? 'idle' : 'error';
    } catch (e) {
      compileErrors = [`Compile failed: ${e}`];
      deployStatus = 'error';
    }
  }

  // ── Deploy ──

  /** Deploy compiled manifest via PDS XRPC. */
  async function handleDeploy() {
    if (!bpmnModeler || !actorDid || !actorName || !actorNanoid) {
      deployMessage = 'Actor DID, name, and nanoid are required';
      deployStatus = 'error';
      return;
    }

    deployStatus = 'deploying';
    deployMessage = '';

    try {
      const { xml } = await bpmnModeler.saveXML({ format: true });

      let dmnXml: string | undefined;
      if (dmnModeler) {
        try { dmnXml = (await dmnModeler.saveXML({ format: true })).xml; } catch { /* */ }
      }

      let formSchemas: Record<string, unknown> | undefined;
      if (formsEditor) {
        try {
          const schema = formsEditor.getSchema();
          if (schema) formSchemas = { default: schema };
        } catch { /* */ }
      }

      const result = await atProcedure('com.etzhayyim.actor.deployProcess', {
        bpmnXml: xml,
        did: actorDid,
        name: actorName,
        nanoid: actorNanoid,
        dmnXml,
        formSchemas,
      }) as { deployed: boolean; executionTier: string; stepsCount: number; warnings: string[] };

      if (result.deployed) {
        deployStatus = 'success';
        deployMessage = `Deployed: ${actorDid} (${result.executionTier}, ${result.stepsCount} steps)`;
      } else {
        deployStatus = 'error';
        deployMessage = 'Deploy failed';
      }
    } catch (e) {
      deployStatus = 'error';
      deployMessage = `Deploy error: ${e}`;
    }
  }
</script>

<div class="flex flex-col h-full bg-[var(--gv2-bg-primary)] text-[var(--gv2-text-primary)]">
  <!-- Header -->
  <div class="flex items-center justify-between px-4 py-3 border-b border-[var(--gv2-border)]">
    <h1 class="text-lg font-semibold">Actor Designer</h1>
    <div class="flex items-center gap-2">
      <input
        bind:value={actorDid}
        placeholder="did:web:actor.etzhayyim.com"
        class="px-2 py-1 text-sm rounded bg-[var(--gv2-bg-secondary)] border border-[var(--gv2-border)] w-48"
      />
      <input
        bind:value={actorName}
        placeholder="actor-name"
        class="px-2 py-1 text-sm rounded bg-[var(--gv2-bg-secondary)] border border-[var(--gv2-border)] w-32"
      />
      <input
        bind:value={actorNanoid}
        placeholder="nanoid"
        class="px-2 py-1 text-sm rounded bg-[var(--gv2-bg-secondary)] border border-[var(--gv2-border)] w-24"
      />
      <button
        onclick={handleDeploy}
        disabled={deployStatus === 'deploying' || !actorDid}
        class="px-4 py-1.5 text-sm font-medium rounded-lg bg-purple-600 text-white hover:bg-purple-700 disabled:opacity-50 transition-colors"
      >
        {deployStatus === 'deploying' ? 'Deploying...' : 'Deploy'}
      </button>
    </div>
  </div>

  <!-- Status bar -->
  {#if deployMessage}
    <div class="px-4 py-2 text-sm {deployStatus === 'success' ? 'bg-green-900/30 text-green-400' : 'bg-red-900/30 text-red-400'}">
      {deployMessage}
    </div>
  {/if}

  <!-- Tab bar -->
  <div class="flex border-b border-[var(--gv2-border)]">
    {#each ['bpmn', 'dmn', 'forms', 'preview'] as tab}
      <button
        onclick={() => switchTab(tab as typeof activeTab)}
        class="px-4 py-2 text-sm font-medium transition-colors
          {activeTab === tab ? 'border-b-2 border-purple-500 text-purple-400' : 'text-[var(--gv2-text-secondary)] hover:text-[var(--gv2-text-primary)]'}"
      >
        {tab === 'bpmn' ? 'BPMN Process' : tab === 'dmn' ? 'DMN Decisions' : tab === 'forms' ? 'Forms' : 'Preview'}
      </button>
    {/each}
  </div>

  <!-- Editor panels -->
  <div class="flex-1 relative overflow-hidden">
    <!-- BPMN Editor -->
    <div bind:this={bpmnContainer} class="absolute inset-0 {activeTab === 'bpmn' ? '' : 'hidden'}"></div>

    <!-- DMN Editor -->
    <div bind:this={dmnContainer} class="absolute inset-0 {activeTab === 'dmn' ? '' : 'hidden'}">
      {#if !dmnModeler}
        <div class="flex items-center justify-center h-full text-[var(--gv2-text-secondary)]">
          <p>DMN editor loading... (requires dmn-js dependency)</p>
        </div>
      {/if}
    </div>

    <!-- Forms Editor -->
    <div bind:this={formsContainer} class="absolute inset-0 {activeTab === 'forms' ? '' : 'hidden'}">
      {#if !formsEditor}
        <div class="flex items-center justify-center h-full text-[var(--gv2-text-secondary)]">
          <p>Forms editor loading... (requires @bpmn-io/form-js-editor dependency)</p>
        </div>
      {/if}
    </div>

    <!-- Preview -->
    {#if activeTab === 'preview'}
      <div class="absolute inset-0 overflow-auto p-4">
        {#if compileErrors.length > 0}
          <div class="mb-4 p-3 rounded-lg bg-red-900/20 border border-red-800">
            <h3 class="text-sm font-semibold text-red-400 mb-1">Errors</h3>
            {#each compileErrors as error}
              <p class="text-sm text-red-300">{error}</p>
            {/each}
          </div>
        {/if}
        {#if compileWarnings.length > 0}
          <div class="mb-4 p-3 rounded-lg bg-yellow-900/20 border border-yellow-800">
            <h3 class="text-sm font-semibold text-yellow-400 mb-1">Warnings</h3>
            {#each compileWarnings as warning}
              <p class="text-sm text-yellow-300">{warning}</p>
            {/each}
          </div>
        {/if}
        {#if compiledManifest}
          <pre class="text-sm font-mono bg-[var(--gv2-bg-secondary)] p-4 rounded-lg overflow-auto">{JSON.stringify(compiledManifest, null, 2)}</pre>
        {:else}
          <div class="flex items-center justify-center h-full text-[var(--gv2-text-secondary)]">
            <p>Click compile to preview the ActorManifest</p>
          </div>
        {/if}
      </div>
    {/if}
  </div>
</div>
