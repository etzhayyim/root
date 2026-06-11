<svelte:options customElement="etzhayyim-project-sre-toolbar" />

<script lang="ts">
  import { AietzhayyimProjectSreToolbar, submitFeedbackViaMcp } from '@sre-shared';

  let { authToken = '', mcpEndpoint = 'https://sre-toolbar.etzhayyim.com/xrpc' } = $props<{
    authToken?: string;
    mcpEndpoint?: string;
  }>();

  async function onSubmitFeedback(payload: { content: string; 'page_url': string; 'component_id': string }) {
    await submitFeedbackViaMcp({
      endpoint: mcpEndpoint,
      authToken,
      input: payload
    });
    return true;
  }
</script>

<div class="host">
  <AietzhayyimProjectSreToolbar pageUrl={window.location.href} onSubmitFeedback={onSubmitFeedback} />
</div>

<style>
  :host {
    position: fixed;
    bottom: 16px;
    right: 16px;
    z-index: 2147483647;
  }
</style>
