<script lang="ts">
  interface Props {
    gaId?: string;
  }

  const { gaId }: Props = $props();

  function isSensitiveHash(hash: string): boolean {
    return hash.startsWith('#auth=');
  }

  $effect(() => {
    if (!gaId || typeof document === 'undefined') {
      return;
    }

    const scriptId = `gtag-${gaId}`;
    const w = window as typeof window & {
      dataLayer?: unknown[];
      gtag?: (...args: unknown[]) => void;
      __gftdGaTrackerInstalled?: boolean;
      __gftdGaCurrentUrl?: string;
    };

    if (!document.getElementById(scriptId)) {
      const script = document.createElement('script');
      script.id = scriptId;
      script.async = true;
      script.src = `https://www.googletagmanager.com/gtag/js?id=${gaId}`;
      document.head.appendChild(script);
    }

    w.dataLayer = w.dataLayer ?? [];
    w.gtag ??= (...args: unknown[]) => {
      w.dataLayer?.push(args);
    };

    w.gtag('js', new Date());
    w.gtag('config', gaId, { 'send_page_view': false });

    const emitPageView = () => {
      if (isSensitiveHash(window.location.hash)) {
        return;
      }
      const sanitizedUrl = `${window.location.origin}${window.location.pathname}${window.location.search}`;
      const sanitizedPath = `${window.location.pathname}${window.location.search}`;
      const url = sanitizedUrl;
      if (w.__gftdGaCurrentUrl === url) {
        return;
      }
      w.__gftdGaCurrentUrl = url;
      w.gtag?.('event', 'page_view', {
        'page_title': document.title,
        'page_location': sanitizedUrl,
        'page_path': sanitizedPath
      });
    };

    emitPageView();

    if (w.__gftdGaTrackerInstalled) {
      return;
    }
    w.__gftdGaTrackerInstalled = true;

    const { history } = window;
    const originalPushState = history.pushState.bind(history);
    const originalReplaceState = history.replaceState.bind(history);
    const dispatchLocationChange = () => window.dispatchEvent(new Event('gftd:ga-locationchange'));

    history.pushState = function (...args) {
      originalPushState(...args);
      dispatchLocationChange();
    };

    history.replaceState = function (...args) {
      originalReplaceState(...args);
      dispatchLocationChange();
    };

    const handleLocationChange = () => emitPageView();
    window.addEventListener('popstate', handleLocationChange);
    window.addEventListener('hashchange', handleLocationChange);
    window.addEventListener('gftd:ga-locationchange', handleLocationChange);

    return () => {
      window.removeEventListener('popstate', handleLocationChange);
      window.removeEventListener('hashchange', handleLocationChange);
      window.removeEventListener('gftd:ga-locationchange', handleLocationChange);
      history.pushState = originalPushState;
      history.replaceState = originalReplaceState;
      w.__gftdGaTrackerInstalled = false;
    };
  });
</script>
